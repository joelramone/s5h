from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, IPvAnyAddress, field_validator


class EnvironmentConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(min_length=1, description="Nombre del ambiente")
    ip: IPvAnyAddress = Field(description="IP del servidor")
    pem_file: str = Field(min_length=1, description="Nombre del archivo PEM")

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        return value.upper()


class AppConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    env_user: str = Field(min_length=1)
    keypair_path: Path
    environments: list[EnvironmentConfig] = Field(default_factory=list)

    @field_validator("keypair_path", mode="before")
    @classmethod
    def parse_keypair_path(cls, value: str | Path) -> Path:
        path = Path(value).expanduser()
        return path

    def find_environment(self, environment_name: str) -> EnvironmentConfig:
        normalized_name = environment_name.upper().strip()
        for environment in self.environments:
            if environment.name == normalized_name:
                return environment
        raise ValueError(f"Ambiente no encontrado: {normalized_name}")

    def upsert_environment(self, environment: EnvironmentConfig) -> None:
        for index, current in enumerate(self.environments):
            if current.name == environment.name:
                self.environments[index] = environment
                return
        self.environments.append(environment)

    def remove_environment(self, environment_name: str) -> None:
        normalized_name = environment_name.upper().strip()
        self.environments = [item for item in self.environments if item.name != normalized_name]
