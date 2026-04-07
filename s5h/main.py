from __future__ import annotations

import argparse
from pathlib import Path

from s5h.repository import ConfigRepository
from s5h.tui import SSHManagerApp


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Gestor SSH para ambientes")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("~/.config/s5h/config.json").expanduser(),
        help="Ruta del archivo de configuración JSON",
    )
    parser.add_argument(
        "--bootstrap-dotenv",
        type=Path,
        default=None,
        help="Importa datos desde un .env y guarda en el config",
    )
    parser.add_argument(
        "--keypair-path",
        type=Path,
        default=None,
        help="Ruta base de PEM para bootstrap",
    )
    return parser


def run() -> None:
    parser = build_parser()
    args = parser.parse_args()

    repository = ConfigRepository(args.config)

    if args.bootstrap_dotenv:
        repository.bootstrap_from_dotenv(args.bootstrap_dotenv, args.keypair_path)

    app = SSHManagerApp(repository)
    app.run()


if __name__ == "__main__":
    run()
