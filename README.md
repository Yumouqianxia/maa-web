## MAA 远程控制平台

该项目提供一个可扩展的 MaaAssistantArknights（MAA）远程控制平台，包含：

- **FastAPI 后端**：实现官方 Remote Control Schema 的 `/maa/getTask`、`/maa/reportStatus`，并提供管理 API。
- **Python Agent**：运行在安卓 Termux Ubuntu（或任意 Linux/macOS）环境中，轮询任务并调用 `maa-cli`。
- **React 控制台**：展示设备与任务状态，可下发「一键长草」「刷关」等指令。

目录大致结构：

```
backend/   # FastAPI 应用
agent/     # maa-cli 轮询 Agent
frontend/  # React + Vite 控制台
```

---

## 1. 后端（FastAPI）

### 1.1 依赖安装

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows 使用 .venv\Scripts\activate
pip install -e .
```

> 如若 `-e` 安装因包发现报错，可直接 `pip install fastapi uvicorn[standard] sqlalchemy alembic ...`（参考 `pyproject.toml`）。

### 1.2 启动

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

默认 SQLite 数据库位于 `backend/data/maa_remote.db`。首次启动会自动建表。

### 1.3 管理 API 快速体验

- `GET /api/devices?user=demo-user`
- `GET /api/devices/{device_id}/tasks?user=demo-user`
- `POST /api/devices/{device_id}/tasks?user=demo-user`

可结合 `curl` 或 `httpie` 手动测试。也可运行脚本预置数据：

```bash
PYTHONPATH=backend/. python backend/scripts/seed_demo_task.py
# 或
PYTHONPATH=backend/. python backend/scripts/smoke_maa_flow.py
```

`smoke_maa_flow.py` 内部会用 FastAPI TestClient 拉取/上报任务，便于在未运行 uvicorn、未接入 agent 时验证链路。

---

## 2. Agent（Termux Ubuntu / Linux / macOS）

### 2.1 安装

```bash
cd agent
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 2.2 配置

复制样例并修改：

```bash
cp config.example.yaml config.yaml
```

关键字段：

- `server_base`：后端地址，例如 `http://192.168.1.100:8000`
- `user_key`：后端使用的用户键（默认 `demo-user`）
- `device_id`：建议为设备唯一 ID
- `maa_binary`：`maa` 可执行文件路径，可在 mac/Linux 先用脚本模拟
- `work_dir`、`env`：指定运行目录与额外环境变量（如 `LD_LIBRARY_PATH`）

### 2.3 运行

```bash
python agent.py --config config.yaml -v
```

Agent 会：

1. 每隔 `poll_interval`（默认 2 秒）拉取 `/maa/getTask`。
2. 将任务映射为 `maa` 命令，目前支持：
   - `LinkStart` → `maa run daily`
   - `Fight` + `params.stage`
3. 捕获 stdout/stderr，截断日志，POST 至 `/maa/reportStatus`。

> macOS 可直接跑上述 agent + `maa`（或 mock 脚本）模拟安卓 Ubuntu 容器；需要时再迁移到 Termux。

---

## 3. React 控制台

### 3.1 安装 & 开发

```bash
cd frontend
npm install
npm run dev
```

默认读取 `.env` 中的 `VITE_API_BASE`、`VITE_DEFAULT_USER_KEY`；如未配置，回退到 `http://127.0.0.1:8000` 与 `demo-user`。

### 3.2 构建

```bash
npm run build
```

产物位于 `frontend/dist/`，可用任意静态服务器（如 `npm run preview`、Nginx）托管。

### 3.3 功能概览

- 设备列表 + 状态、最后心跳；
- 设备详情：Agent 版本、操作按钮；
- 快捷任务：一键长草/刷关（可自扩展更多 task type）；
- 任务列表：展示最新日志、状态、时间戳。

---

## 4. 本地联调流程（无需安卓）

1. **后端**：`uvicorn app.main:app --reload --port 8000`
2. **预置任务**：运行 `seed_demo_task.py` 或通过管理 API 创建。
3. **Agent**：在 mac/Linux 运行 `python agent.py --config config.yaml -v`，`maa_binary` 可暂指向 mock shell 脚本。
4. **前端**：`npm run dev`，浏览器访问 `http://localhost:5173`（Vite 默认端口），即可看到 demo 设备与任务。

冒烟验证（无 agent）可直接运行：

```bash
PYTHONPATH=backend/. python backend/scripts/smoke_maa_flow.py
```

输出会显示 `getTask`/`reportStatus` 的模拟结果。

---

## 5. 生产部署建议

- 数据库：SQLite 可换成 PostgreSQL/MySQL；只需调整 `MAA_DATABASE_URL` 环境变量。
- 后端部署：使用 `gunicorn -k uvicorn.workers.UvicornWorker app.main:app` 并置于反向代理之后。
- Agent：配置 systemd/tmux/supervisor 常驻；注意 `device_id` 唯一且与后端用户键对应。
- 前端：`npm run build` 后将 `dist/` 部署到 CDN 或 Nginx，并在 `.env` 中指向线上 API。

---

## 6. 后续规划

- 扩展更多任务类型（基建、公招、理智药配置等）；
- `/maa/getTask` 支持批量任务、任务优先级；
- 设备/任务 WebSocket 推送；
- 引入用户鉴权、API Token；
- 集成截图、日志下载等可视化能力。

欢迎基于此 MVP 继续演进。若需要进一步协助（如 Docker 部署、CI、测试用例等），可在 Issue/PR 中提出。 :)

