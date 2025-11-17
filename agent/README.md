# MAA CLI Agent

该目录提供运行在安卓 Termux Ubuntu 容器中的 maa-cli 轮询 Agent，实现与后端远控服务器的 `/maa/getTask` 与 `/maa/reportStatus` 协议互通。

## 环境准备

```bash
sudo apt update && sudo apt install -y python3 python3-venv python3-pip
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .
```

> `pip install -e .` 会根据 `pyproject.toml` 安装 `httpx`、`pydantic`、`PyYAML`、`typer` 等依赖。

## 配置

1. 复制示例配置：

   ```bash
   cp config.example.yaml config.yaml
   ```

2. 调整以下关键字段：
   - `server_base`：后端服务地址，例如 `http://192.168.1.100:8000`
   - `user_key`：在后端预先创建/约定的用户键
   - `device_id`：建议为当前设备固定字符串，便于后端识别
   - `maa_binary`：Termux Ubuntu 内 `maa` 可执行文件路径
   - `work_dir`：`maa` 运行目录（保存配置、资源、日志等）

## 运行

```bash
python agent.py --config config.yaml
```

支持参数：

- `--config/-c`：指定配置文件路径，默认为当前目录 `config.yaml`
- `--verbose/-v`：输出更多调试日志

## 任务映射

当前内置任务类型与命令映射如下：

| 任务类型    | maa-cli 命令示例           |
| ---------- | -------------------------- |
| LinkStart  | `maa run daily`            |
| Fight      | `maa fight <stage>` 需要 `params.stage` |

未识别的任务类型会被视为失败并上报后端，便于扩展其他模式（基建、公招等）。

## 日志

- Agent 日志输出至控制台，可结合 `tmux`/`screen` 常驻运行。
- 上报后端的执行日志会被截断至 `report_log_max_chars`（默认 4000 字符）以避免爆表。

## 注意事项

- 确保 `maa` 命令在 PATH 中或通过 `maa_binary` 指明完整路径。
- 如需额外依赖（例如 `LD_LIBRARY_PATH`），可在配置文件的 `env` 节设置。
- 生产环境建议为每台设备分配唯一 `device_id`，避免任务混乱。

