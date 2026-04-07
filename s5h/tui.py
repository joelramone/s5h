from __future__ import annotations

from pathlib import Path

from textual import on
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, DataTable, Footer, Header, Input, Label, Static

from s5h.models import AppConfig, EnvironmentConfig
from s5h.repository import ConfigRepository
from s5h.service import SSHService


class MessageScreen(ModalScreen[None]):
    def __init__(self, message: str) -> None:
        super().__init__()
        self.message = message

    def compose(self) -> ComposeResult:
        with Vertical(id="message-modal"):
            yield Static(self.message)
            yield Button("Cerrar", id="close-message")

    @on(Button.Pressed, "#close-message")
    def close_modal(self) -> None:
        self.dismiss()


class EditEnvironmentScreen(ModalScreen[EnvironmentConfig | None]):
    def __init__(self, initial: EnvironmentConfig | None = None) -> None:
        super().__init__()
        self.initial = initial

    def compose(self) -> ComposeResult:
        with Vertical(id="edit-environment-modal"):
            yield Label("Ambiente")
            yield Input(value=self.initial.name if self.initial else "", id="env-name")
            yield Label("IP")
            yield Input(value=str(self.initial.ip) if self.initial else "", id="env-ip")
            yield Label("Archivo PEM")
            yield Input(value=self.initial.pem_file if self.initial else "", id="env-pem")
            with Horizontal():
                yield Button("Guardar", id="save-env", variant="success")
                yield Button("Cancelar", id="cancel-env")

    @on(Button.Pressed, "#save-env")
    def save_environment(self) -> None:
        try:
            name = self.query_one("#env-name", Input).value
            ip = self.query_one("#env-ip", Input).value
            pem_file = self.query_one("#env-pem", Input).value
            environment = EnvironmentConfig(name=name, ip=ip, pem_file=pem_file)
            self.dismiss(environment)
        except Exception as error:  # pylint: disable=broad-except
            self.app.push_screen(MessageScreen(f"Error: {error}"))

    @on(Button.Pressed, "#cancel-env")
    def cancel(self) -> None:
        self.dismiss(None)


class KeypairPathScreen(ModalScreen[Path | None]):
    def __init__(self, current_path: Path) -> None:
        super().__init__()
        self.current_path = current_path

    def compose(self) -> ComposeResult:
        with Vertical(id="path-modal"):
            yield Label("Ruta de keypair")
            yield Input(value=str(self.current_path), id="keypair-path")
            with Horizontal():
                yield Button("Guardar", id="save-path", variant="success")
                yield Button("Cancelar", id="cancel-path")

    @on(Button.Pressed, "#save-path")
    def save_path(self) -> None:
        try:
            path_input = self.query_one("#keypair-path", Input).value
            validated = SSHService.validate_keypair_path(path_input)
            self.dismiss(validated)
        except Exception as error:  # pylint: disable=broad-except
            self.app.push_screen(MessageScreen(f"Error: {error}"))

    @on(Button.Pressed, "#cancel-path")
    def cancel(self) -> None:
        self.dismiss(None)


class SSHManagerApp(App[None]):
    TITLE = "S5H SSH Manager"
    BINDINGS = [
        ("a", "add_environment", "Agregar ambiente"),
        ("e", "edit_environment", "Editar ambiente"),
        ("d", "delete_environment", "Eliminar ambiente"),
        ("c", "connect_environment", "Conectar"),
        ("p", "set_keypair_path", "Ruta keypair"),
        ("s", "save", "Guardar"),
        ("q", "quit", "Salir"),
    ]

    def __init__(self, repository: ConfigRepository) -> None:
        super().__init__()
        self.repository = repository
        self.config_data = repository.load()

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("Ambientes configurados", id="title")
        yield DataTable(id="env-table")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("Ambiente", "IP", "PEM")
        self.refresh_table()

    def refresh_table(self) -> None:
        table = self.query_one(DataTable)
        table.clear()
        ordered = sorted(self.config_data.environments, key=lambda item: item.name)
        for environment in ordered:
            table.add_row(environment.name, str(environment.ip), environment.pem_file, key=environment.name)

    def _selected_environment_name(self) -> str | None:
        table = self.query_one(DataTable)
        if table.cursor_row < 0:
            return None
        row_key, _ = table.coordinate_to_cell_key((table.cursor_row, 0))
        return str(row_key.value) if row_key else None

    def action_add_environment(self) -> None:
        def handler(result: EnvironmentConfig | None) -> None:
            if result is None:
                return
            self.config_data.upsert_environment(result)
            self.refresh_table()

        self.push_screen(EditEnvironmentScreen(), handler)

    def action_edit_environment(self) -> None:
        selected_name = self._selected_environment_name()
        if not selected_name:
            self.push_screen(MessageScreen("Selecciona un ambiente para editar"))
            return

        current = self.config_data.find_environment(selected_name)

        def handler(result: EnvironmentConfig | None) -> None:
            if result is None:
                return
            self.config_data.upsert_environment(result)
            self.refresh_table()

        self.push_screen(EditEnvironmentScreen(current), handler)

    def action_delete_environment(self) -> None:
        selected_name = self._selected_environment_name()
        if not selected_name:
            self.push_screen(MessageScreen("Selecciona un ambiente para eliminar"))
            return
        self.config_data.remove_environment(selected_name)
        self.refresh_table()

    def action_connect_environment(self) -> None:
        selected_name = self._selected_environment_name()
        if not selected_name:
            self.push_screen(MessageScreen("Selecciona un ambiente para conectar"))
            return

        try:
            service = SSHService(self.config_data)
            command = service.build_command(selected_name)
            with self.suspend():
                service.connect_with_command(command)
            self.push_screen(MessageScreen(f"Conexión finalizada: {' '.join(command)}"))
        except Exception as error:  # pylint: disable=broad-except
            self.push_screen(MessageScreen(f"Error: {error}"))

    def action_set_keypair_path(self) -> None:
        def handler(result: Path | None) -> None:
            if result is None:
                return
            self.config_data.keypair_path = result

        self.push_screen(KeypairPathScreen(self.config_data.keypair_path), handler)

    def action_save(self) -> None:
        self.repository.save(self.config_data)
        self.push_screen(MessageScreen("Configuración guardada"))
