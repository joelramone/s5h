from __future__ import annotations

import json
from pathlib import Path

from dotenv import dotenv_values

from s5h.models import AppConfig, EnvironmentConfig


class ConfigRepository:
    def __init__(self, config_path: Path) -> None:
        self.config_path = config_path.expanduser()

    def load(self) -> AppConfig:
        if not self.config_path.exists():
            return AppConfig(env_user="ec2-user", keypair_path=Path("~/.ssh"), environments=[])

        payload = json.loads(self.config_path.read_text(encoding="utf-8"))
        return AppConfig.model_validate(payload)

    def save(self, config: AppConfig) -> None:
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text(
            json.dumps(config.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def bootstrap_from_dotenv(self, dotenv_path: Path, keypair_path: Path | None = None) -> AppConfig:
        values = dotenv_values(dotenv_path)

        env_user = (values.get("ENV_USER") or "ec2-user").strip()
        resolved_keypair_path = keypair_path or Path(values.get("KEYPAIR_PATH") or "~/.ssh")

        environments: list[EnvironmentConfig] = []
        for key, value in values.items():
            if not key.startswith("IP_"):
                continue
            environment_name = key.removeprefix("IP_").strip().upper()
            ip = str(value).strip()
            pem_candidate = values.get(f"PEM_{environment_name}") or f"{environment_name.lower()}.pem"
            environments.append(
                EnvironmentConfig(name=environment_name, ip=ip, pem_file=str(pem_candidate).strip())
            )

        config = AppConfig(env_user=env_user, keypair_path=resolved_keypair_path, environments=environments)
        self.save(config)
        return config
