<p align="center">
  <a href="README.ru.md">
    <img src="https://img.shields.io/badge/Язык-🇷🇺%20Русский-blue?style=for-the-badge" alt="Русский">
  </a>
  &nbsp;&nbsp;
  <a href="README.md">
    <img src="https://img.shields.io/badge/Language-🇬🇧%20English-2ea44f?style=for-the-badge" alt="English">
  </a>
</p>

# 🏛️ Каталог плагинов и расширений для Hermes

Модульный каталог плагинов и интерфейсных расширений для [Hermes Desktop](https://github.com/NousResearch/hermes-agent).

Каждый модуль изолирован в своей папке `plugins/<имя-плагина>` со своей собственной инструкцией, файлами и скриптами быстрой установки в 1 клик.

---

## 🌟 Доступные плагины

| Плагин | Описание | Инструкция и установка |
| :--- | :--- | :--- |
| ⚡ **`antigravity-oauth`** | Прямой Google Cloud Code / Antigravity OAuth провайдер (Gemini) без сторонних утилит | [👉 Перейти к плагину](plugins/antigravity-oauth/README.ru.md) |

*(Каталог пополняется новыми модулями)*

---

## 📁 Структура каталога

```text
Hermes/
├── plugins/
│   └── antigravity-oauth/      # ⚡ Плагин «Google Antigravity OAuth»
│       ├── plugin.yaml
│       ├── __init__.py
│       ├── direct.py
│       ├── wire.mjs
│       ├── package.json
│       ├── install.bat
│       ├── install.sh
│       ├── README.md           # (EN)
│       └── README.ru.md        # (RU)
└── README.md
```

---

## 🚀 Как установить нужный плагин

1. Выберите плагин из таблицы выше и перейдите в его папку:
   - **[⚡ Вход Google Antigravity OAuth](plugins/antigravity-oauth/README.ru.md)** — прямое подключение моделей Gemini без сторонних CLI.

2. Внутри папки каждого плагина лежат готовые скрипты установки (`install.bat` для Windows, `install.sh` для Linux/macOS) и пошаговая инструкция.

---

## 🛡️ Безопасность

- Репозиторий **не содержит** персональных токенов, ключей доступа или настроек пользователей.
- Все учетные данные шифруются локально на компьютере пользователя.
