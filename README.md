# s5h-ssh-manager

Gestor de conexiones SSH para CLI (WSL/Linux/macOS) con TUI basada en Textual.

## Características

- Gestión de ambientes desde menú (alta, edición, eliminación).
- Configuración persistente en JSON.
- Conexión SSH usando archivo PEM por ambiente.
- Importación inicial desde `.env`.
- Cambio dinámico de ruta base de keypair.

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Uso

### 1) Ejecutar TUI

```bash
s5h
```

### 2) Bootstrap desde `.env`

```bash
s5h --bootstrap-dotenv /ruta/al/.env --keypair-path "/home/jd0519/My Documents/ubuntu_files/scripts/s5h/kyepair"
```

## Formato de configuración (`~/.config/s5h/config.json`)

```json
{
  "env_user": "ec2-user",
  "keypair_path": "/home/jd0519/My Documents/ubuntu_files/scripts/s5h/kyepair",
  "environments": [
    {
      "name": "LAB",
      "ip": "10.223.24.250",
      "pem_file": "lab.pem"
    }
  ]
}
```
