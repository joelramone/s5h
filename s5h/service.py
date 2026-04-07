from __future__ import annotations

import subprocess
from pathlib import Path

from s5h.models import AppConfig


class SSHService:
    def __init__(self, config: AppConfig) -> None:
        self.config = config

    def build_command(self, environment_name: str) -> list[str]:
        environment = self.config.find_environment(environment_name)
        pem_path = (self.config.keypair_path / environment.pem_file).expanduser()

        if not pem_path.exists():
            raise FileNotFoundError(f"No existe el archivo PEM: {pem_path}")

        return ["ssh", "-i", str(pem_path), f"{self.config.env_user}@{environment.ip}"]

    def connect(self, environment_name: str) -> int:
        command = self.build_command(environment_name)
        result = subprocess.run(command, check=False)
        return result.returncode

    @staticmethod
    def validate_keypair_path(path: str) -> Path:
        candidate = Path(path).expanduser()
        if not candidate.exists():
            raise ValueError(f"La ruta no existe: {candidate}")
        if not candidate.is_dir():
            raise ValueError(f"La ruta no es un directorio: {candidate}")
        return candidate
