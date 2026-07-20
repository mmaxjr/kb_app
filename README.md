# NOTE MAX

Base de conhecimento pessoal (KivyMD) para incidentes e soluções técnicas, com notas sincronizadas no Notion, cache offline em SQLite e senha mestra protegendo o token de integração.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Você também precisa criar uma integration no Notion (https://www.notion.so/my-integrations), copiar o token e compartilhar o database de notas com ela. Defina o `database_id` em `services/notion_service.py` (ou passe-o ao instanciar `NotionService`).

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

O workflow em `.github/workflows/build-apk.yml` builda automaticamente via GitHub Actions (aba **Actions → Build APK → Run workflow**), incluindo o download best-effort das fontes da marca.

## Identidade visual

- Fundo `#05070A`, superfície `#10161F`, acento `#00E6B8`, alerta `#FFB454`.
- Tipografia: Space Grotesk (títulos) + JetBrains Mono (labels técnicos), com fallback automático para a fonte padrão do Kivy caso os `.ttf` não estejam presentes no build (ver `main.py::_register_brand_fonts`).
- Cores centralizadas em `theme.py` e aplicadas globalmente via `kv/theme.kv`.

## Estrutura

```
kb_app/
├── main.py
├── theme.py           # paleta e nomes de fonte da marca
├── screens/            # telas (lock, lista, detalhe, criação)
├── services/           # Notion API, criptografia, cache SQLite
├── models/              # dataclass Ticket
├── assets/              # ícone, presplash e fontes da marca
├── kv/                  # layouts .kv (theme.kv define o estilo global)
└── buildozer.spec
```
