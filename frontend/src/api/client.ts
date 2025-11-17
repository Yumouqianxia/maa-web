import type { Device, Task, TaskCreatePayload } from "./types";

const API_BASE = (import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000").replace(
  /\/$/,
  "",
);

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });

  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(text || resp.statusText);
  }

  if (resp.status === 204) {
    return undefined as T;
  }

  return (await resp.json()) as T;
}

export async function fetchDevices(userKey?: string): Promise<Device[]> {
  const params = new URLSearchParams();
  if (userKey) {
    params.append("user", userKey);
  }
  const query = params.toString();
  const path = query ? `/api/devices?${query}` : "/api/devices";
  return request<Device[]>(path);
}

export async function fetchDeviceTasks(
  deviceId: string,
  userKey: string,
  limit = 20,
): Promise<Task[]> {
  const params = new URLSearchParams({
    user: userKey,
    limit: String(limit),
  });
  return request<Task[]>(`/api/devices/${encodeURIComponent(deviceId)}/tasks?${params}`);
}

export async function createTaskForDevice(
  deviceId: string,
  userKey: string,
  payload: TaskCreatePayload,
): Promise<Task> {
  const params = new URLSearchParams({ user: userKey });
  return request<Task>(`/api/devices/${encodeURIComponent(deviceId)}/tasks?${params}`, {
    method: "POST",
    body: JSON.stringify({
      type: payload.type,
      params: payload.params ?? {},
      priority: payload.priority ?? 0,
    }),
  });
}

