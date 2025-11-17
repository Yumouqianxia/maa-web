export type TaskStatus = "Pending" | "Running" | "Succeeded" | "Failed" | "Cancelled";

export interface Device {
  id: number;
  user_key: string;
  device_id: string;
  display_name?: string | null;
  status: string;
  agent_version?: string | null;
  last_seen_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface Task {
  id: number;
  task_uuid: string;
  user_key: string;
  device_identifier: string;
  type: string;
  payload: Record<string, unknown>;
  status: TaskStatus;
  priority: number;
  created_at: string;
  started_at?: string | null;
  finished_at?: string | null;
  log?: string | null;
  error_message?: string | null;
}

export interface TaskCreatePayload {
  type: string;
  params?: Record<string, unknown>;
  priority?: number;
}

