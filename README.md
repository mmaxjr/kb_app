# KB App

App de base de conhecimento (KivyMD) com tickets sincronizados no Notion, cache offline em SQLite e senha mestra protegendo o token de integração.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Você também precisa criar uma integration no Notion (https://www.notion.so/my-integrations), copiar o token e compartilhar o database de tickets com ela. Defina o `database_id` em `services/notion_service.py` (ou passe-o ao instanciar `NotionService`).

## Rodar localmente

```bash
python main.py
```

Na primeira execução, o app pede o token de integration do Notion e uma senha mestra — o token é criptografado (Fernet, chave derivada por SHA-256 da senha) e salvo em `secure_data.json`. Nas próximas vezes, basta digitar a senha mestra.

## Build Android

```bash
buildozer android debug
```

Gera o `.apk` em `bin/`. Para iOS, use `kivy-ios` (processo via Xcode, mais manual).

## Estrutura

```
kb_app/
├── main.py
├── screens/        # telas (lock, lista, detalhe, criação)
├── services/        # Notion API, criptografia, cache SQLite
├── models/           # dataclass Ticket
├── kv/                # layouts .kv
└── buildozer.spec
```
