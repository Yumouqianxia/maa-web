"""maa-cli polling agent."""

from __future__ import annotations

import logging
import os
import subprocess
import time
from pathlib import Path
from typing import Any
from uuid import uuid4

import httpx
import typer
import yaml
from pydantic import BaseModel, Field, PositiveFloat

app = typer.Typer(help="maa-cli remote control polling agent.")
logger = logging.getLogger("maa_agent")


class TaskStatus(str):
    """Mirror of server side task status values."""

    SUCCEEDED = "Succeeded"
    FAILED = "Failed"


class AgentConfig(BaseModel):
    """Runtime configuration loaded from YAML."""

    server_base: str = Field(description="Backend base URL, e.g. http://127.0.0.1:8000")
    user_key: str = Field(description="Shared user key for authenticating with server.")
    device_id: str | None = Field(default=None, description="Unique device identifier.")
    poll_interval: PositiveFloat = Field(
        default=2.0, description="Seconds between task polling requests."
    )
    maa_binary: str = Field(default="maa", description="Path to maa-cli executable.")
    work_dir: str | None = Field(
        default=None, description="Working directory where maa-cli runs."
    )
    agent_version: str = Field(default="maa-termux-agent/0.1.0")
    get_task_path: str = Field(default="/maa/getTask")
    report_status_path: str = Field(default="/maa/reportStatus")
    request_timeout: PositiveFloat = Field(default=30.0)
    report_log_max_chars: int = Field(default=4000)
    env: dict[str, str] = Field(
        default_factory=dict, description="Extra environment variables for maa-cli."
    )

    def normalized_server_base(self) -> str:
        """Ensure server base URL has no trailing slash."""

        return self.server_base.rstrip("/")


def load_config(path: Path) -> AgentConfig:
    """Load YAML config file into AgentConfig."""

    with path.open("r", encoding="utf-8") as fp:
        data = yaml.safe_load(fp) or {}
    return AgentConfig(**data)


class MaaCliAgent:
    """Long-running polling agent orchestrating maa-cli commands."""

    def __init__(self, config: AgentConfig) -> None:
        self.config = config
        self.device_id = config.device_id or uuid4().hex
        if config.device_id is None:
            logger.warning(
                "未在配置中提供 device_id，当前会话将使用临时 ID：%s", self.device_id
            )
        self._client = httpx.Client(
            base_url=self.config.normalized_server_base(),
            timeout=self.config.request_timeout,
        )

    def run(self) -> None:
        """Main polling loop."""

        logger.info("MAA agent 启动，设备 %s", self.device_id)
        while True:
            try:
                tasks = self.fetch_tasks()
                if not tasks:
                    time.sleep(self.config.poll_interval)
                    continue
                for task in tasks:
                    self.process_task(task)
            except KeyboardInterrupt:
                logger.info("收到中断信号，正在退出...")
                raise
            except Exception as exc:  # pylint: disable=broad-except
                logger.exception("轮询任务时发生异常: %s", exc)
                time.sleep(self.config.poll_interval)

    def fetch_tasks(self) -> list[dict[str, Any]]:
        """Call backend to obtain pending tasks."""

        payload = {
            "user": self.config.user_key,
            "device": self.device_id,
            "agentVersion": self.config.agent_version,
        }
        response = self._client.post(self.config.get_task_path, json=payload)
        response.raise_for_status()
        body = response.json()
        tasks = body.get("tasks", [])
        logger.debug("拉取到 %d 个任务", len(tasks))
        return tasks

    def process_task(self, task: dict[str, Any]) -> None:
        """Execute maa-cli for a single task envelope."""

        task_id = task.get("id")
        task_type = task.get("type")
        params = task.get("params") or {}
        logger.info("开始执行任务 %s (%s)", task_id, task_type)
        status = TaskStatus.FAILED
        log_text = ""
        result: dict[str, Any] | None = None

        try:
            command = self.build_command(task_type, params)
            output = self.invoke_maa(command)
            status = TaskStatus.SUCCEEDED
            log_text = output
            result = {"command": command, "returnCode": 0}
        except subprocess.CalledProcessError as exc:
            log_text = self._truncate_log(exc.stdout or "" + exc.stderr or "")
            result = {"command": exc.cmd, "returnCode": exc.returncode}
            logger.error("任务 %s 执行失败：%s", task_id, exc)
        except Exception as exc:  # pylint: disable=broad-except
            log_text = self._truncate_log(repr(exc))
            logger.exception("任务 %s 执行过程中异常", task_id)
        finally:
            self.report_status(
                task_id=task_id,
                status=status,
                log=log_text,
                result=result,
            )

    def build_command(self, task_type: str, params: dict[str, Any]) -> list[str]:
        """Translate Maa remote task into maa-cli command."""

        binary = self.config.maa_binary

        if task_type == "LinkStart":
            return [binary, "run", "daily"]
        if task_type == "Fight":
            stage = params.get("stage")
            if not stage:
                raise ValueError("Fight 任务需要 `stage` 参数")
            return [binary, "fight", str(stage)]

        raise ValueError(f"未知任务类型: {task_type}")

    def invoke_maa(self, command: list[str]) -> str:
        """Execute maa-cli command and return captured logs."""

        env = os.environ.copy()
        env.update(self.config.env)
        work_dir = Path(self.config.work_dir).expanduser() if self.config.work_dir else None
        completed = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=work_dir,
            env=env,
            check=True,
        )
        return self._truncate_log(completed.stdout or "")

    def report_status(
        self,
        *,
        task_id: str,
        status: str,
        log: str | None,
        result: dict[str, Any] | None,
    ) -> None:
        """Send execution result back to backend."""

        log_payload = self._truncate_log(log or "")
        payload = {
            "user": self.config.user_key,
            "device": self.device_id,
            "taskId": task_id,
            "status": status,
            "log": log_payload,
            "result": result,
        }
        logger.debug("汇报任务 %s 状态：%s", task_id, status)
        response = self._client.post(self.config.report_status_path, json=payload)
        response.raise_for_status()

    def _truncate_log(self, text: str) -> str:
        """Ensure logs do not exceed configured length."""

        if len(text) <= self.config.report_log_max_chars:
            return text
        return text[-self.config.report_log_max_chars :]


def configure_logging(verbose: bool = False) -> None:
    """Set up console logging format."""

    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )


@app.command()
def main(
    config: Path = typer.Option(
        Path("config.yaml"),
        "--config",
        "-c",
        help="Configuration file path.",
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable debug logs."),
) -> None:
    """Start the polling loop."""

    configure_logging(verbose)
    try:
        settings = load_config(config)
    except FileNotFoundError:
        typer.echo(f"配置文件 {config} 不存在", err=True)
        raise typer.Exit(code=1) from None
    except Exception as exc:  # pylint: disable=broad-except
        typer.echo(f"解析配置失败: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    agent = MaaCliAgent(settings)
    try:
        agent.run()
    except KeyboardInterrupt:
        typer.echo("已退出")
        raise typer.Exit(code=0) from None


if __name__ == "__main__":
    app()

