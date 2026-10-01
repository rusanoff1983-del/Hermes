<p align="center">
  <a href="README.ru.md">
    <img src="https://img.shields.io/badge/Язык-🇷🇺%20Русский-blue?style=for-the-badge" alt="Русский">
  </a>
  &nbsp;&nbsp;
  <a href="README.md">
    <img src="https://img.shields.io/badge/Language-🇬🇧%20English-2ea44f?style=for-the-badge" alt="English">
  </a>
</p>

# 🏛️ Hermes Plugins & UI Extensions Catalog

A modular catalog of plugins and UI extensions for [Hermes Desktop](https://github.com/NousResearch/hermes-agent).

Each plugin is completely isolated inside its own folder under `plugins/<plugin-name>` with its own documentation, files, and 1-click install scripts.

---

## 🌟 Available Plugins

| Plugin | Description | Documentation & Install |
| :--- | :--- | :--- |
| ⭐ **`favorites-models`** | Compact quick-select button for favorite models directly in the chat header | [👉 Open Plugin](plugins/favorites-models/README.md) |
| ⚡ **`antigravity-oauth`** | Direct Google Cloud Code / Antigravity OAuth provider (Gemini) with zero extra CLI tools | [👉 Open Plugin](plugins/antigravity-oauth/README.md) |

*(New plugins are added regularly)*

---

## 📁 Repository Structure

```text
Hermes/
├── plugins/
│   ├── favorites-models/       # ⭐ Favorite Models Plugin
│   │   ├── plugin.js
│   │   ├── install.bat
│   │   ├── README.md           # (EN)
│   │   └── README.ru.md        # (RU)
│   │
│   └── antigravity-oauth/      # ⚡ Google Antigravity OAuth Plugin
│       ├── plugin.yaml
│       ├── __init__.py
│       ├── direct.py
│       ├── wire.mjs
│       ├── package.json
│       ├── install.bat
│       ├── install.sh
│       ├── README.md           # (EN)
│       └── README.ru.md        # (RU)
│
├── interface/                  # Native Desktop patches & bridges
├── docs/                       # Screenshots & extended documentation
└── README.md
```

---

## 🚀 How to Install a Plugin

1. Choose the desired plugin from the table above and open its folder:
   - **[⭐ Favorite Models Button](plugins/favorites-models/README.md)** — fast model switcher in the chat header.
   - **[⚡ Google Antigravity OAuth](plugins/antigravity-oauth/README.md)** — direct Gemini provider with 1-click browser login.

2. Inside each plugin folder, you will find a **ready-to-use `install.bat`** (1-click installation on Windows) and clear step-by-step instructions.

---

## 🛡️ Security & Privacy

- This repository **never contains** private tokens, API keys, or user configurations.
- All credentials are encrypted locally on your machine using Windows DPAPI / secure storage.

