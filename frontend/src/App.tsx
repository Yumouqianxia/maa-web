import { useEffect, useMemo, useState } from "react";
import "./index.css";
import { createTaskForDevice, fetchDeviceTasks, fetchDevices } from "./api/client";
import type { Device, Task } from "./api/types";

const DEFAULT_USER_KEY = import.meta.env.VITE_DEFAULT_USER_KEY ?? "demo-user";

export function App() {
  const [devices, setDevices] = useState<Device[]>([]);
  const [devicesLoading, setDevicesLoading] = useState(false);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [tasksLoading, setTasksLoading] = useState(false);
  const [selectedDeviceId, setSelectedDeviceId] = useState<string | null>(null);
  const [stageInput, setStageInput] = useState("");
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const selectedDevice = useMemo(
    () => devices.find((d) => d.device_id === selectedDeviceId) ?? null,
    [devices, selectedDeviceId],
  );

  useEffect(() => {
    refreshDevices();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (selectedDeviceId) {
      refreshTasks(selectedDeviceId);
    } else {
      setTasks([]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedDeviceId]);

  async function refreshDevices() {
    setDevicesLoading(true);
    setError(null);
    try {
      const list = await fetchDevices(DEFAULT_USER_KEY);
      setDevices(list);
      if (!selectedDeviceId && list.length > 0) {
        setSelectedDeviceId(list[0].device_id);
      } else if (selectedDeviceId) {
        const stillExists = list.some((d) => d.device_id === selectedDeviceId);
        if (!stillExists) {
          setSelectedDeviceId(list[0]?.device_id ?? null);
        }
      }
    } catch (err) {
      console.error(err);
      setError(err instanceof Error ? err.message : "加载设备失败");
    } finally {
      setDevicesLoading(false);
    }
  }

  async function refreshTasks(deviceId: string) {
    setTasksLoading(true);
    setError(null);
    try {
      const list = await fetchDeviceTasks(deviceId, DEFAULT_USER_KEY, 20);
      setTasks(list);
    } catch (err) {
      console.error(err);
      setError(err instanceof Error ? err.message : "获取任务失败");
    } finally {
      setTasksLoading(false);
    }
  }

  async function enqueueTask(type: string, params: Record<string, unknown>) {
    if (!selectedDeviceId) {
      return;
    }
    setActionLoading(true);
    setError(null);
    try {
      await createTaskForDevice(selectedDeviceId, DEFAULT_USER_KEY, {
        type,
        params,
      });
      await refreshTasks(selectedDeviceId);
    } catch (err) {
      console.error(err);
      setError(err instanceof Error ? err.message : "下发任务失败");
    } finally {
      setActionLoading(false);
    }
  }

  async function handleLinkStart() {
    await enqueueTask("LinkStart", {});
  }

  async function handleFight() {
    if (!stageInput.trim()) {
      setError("请输入关卡号");
      return;
    }
    await enqueueTask("Fight", { stage: stageInput.trim() });
    setStageInput("");
  }

  return (
    <div className="app">
      <header>
        <div>
          <h1>MAA 远程控制台</h1>
          <p className="subtitle">用户：{DEFAULT_USER_KEY}</p>
        </div>
        <button className="ghost" onClick={refreshDevices} disabled={devicesLoading}>
          {devicesLoading ? "刷新中…" : "刷新设备"}
        </button>
      </header>

      {error ? <div className="alert">{error}</div> : null}

      <main className="layout">
        <aside className="sidebar">
          <h2>设备列表</h2>
          {devicesLoading && devices.length === 0 ? (
            <p className="muted">加载中…</p>
          ) : devices.length === 0 ? (
            <p className="muted">暂无设备上线</p>
          ) : (
            <ul className="device-list">
              {devices.map((device) => (
                <li
                  key={device.id}
                  className={
                    device.device_id === selectedDeviceId ? "device-item active" : "device-item"
                  }
                  onClick={() => setSelectedDeviceId(device.device_id)}
                >
                  <div className="device-name">
                    {device.display_name || device.device_id}
                    <span className={`status ${device.status.toLowerCase()}`}>
                      {device.status}
                    </span>
                  </div>
                  <p className="device-meta">
                    最后心跳：{formatTimestamp(device.last_seen_at) ?? "未连接"}
                  </p>
                </li>
              ))}
            </ul>
          )}
        </aside>

        <section className="content">
          {selectedDevice ? (
            <>
              <div className="device-header">
                <div>
                  <h2>{selectedDevice.display_name || selectedDevice.device_id}</h2>
                  <p className="device-meta">
                    Agent {selectedDevice.agent_version ?? "未知"} · 设备 ID {selectedDevice.device_id}
                  </p>
                  <p className="device-meta">
                    最后心跳：{formatTimestamp(selectedDevice.last_seen_at) ?? "未连接"}
                  </p>
                </div>
              </div>

              <div className="actions">
                <button onClick={handleLinkStart} disabled={actionLoading}>
                  {actionLoading ? "执行中…" : "一键长草"}
                </button>
                <div className="fight-form">
                  <input
                    type="text"
                    placeholder="关卡号，例如 1-7"
                    value={stageInput}
                    onChange={(e) => setStageInput(e.target.value)}
                    disabled={actionLoading}
                  />
                  <button onClick={handleFight} disabled={actionLoading}>
                    刷指定关卡
                  </button>
                </div>
              </div>

              <div className="task-panel">
                <div className="task-panel-header">
                  <h3>最近任务</h3>
                  <button className="ghost" onClick={() => refreshTasks(selectedDevice.device_id)}>
                    {tasksLoading ? "刷新中…" : "刷新列表"}
                  </button>
                </div>
                {tasksLoading && tasks.length === 0 ? (
                  <p className="muted">加载中…</p>
                ) : tasks.length === 0 ? (
                  <p className="muted">暂无任务记录</p>
                ) : (
                  <ul className="task-list">
                    {tasks.map((task) => (
                      <li key={task.task_uuid} className="task-item">
                        <div className="task-header">
                          <span className="task-type">{task.type}</span>
                          <span className={`status ${task.status.toLowerCase()}`}>{task.status}</span>
                        </div>
                        <p className="task-meta">
                          创建：{formatTimestamp(task.created_at)} ·
                          状态更新时间：{formatTimestamp(task.finished_at || task.started_at)}
                        </p>
                        {task.log ? (
                          <pre className="task-log">{task.log.slice(-400)}</pre>
                        ) : (
                          <p className="task-meta muted">暂无日志</p>
                        )}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </>
          ) : (
            <div className="placeholder">请选择设备查看详情</div>
          )}
        </section>
      </main>
    </div>
  );
}

function formatTimestamp(value?: string | null): string | null {
  if (!value) {
    return null;
  }
  try {
    return new Date(value).toLocaleString();
  } catch {
    return value;
  }
}

