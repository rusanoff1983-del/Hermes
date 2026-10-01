# Hermes Plugins & UI Extensions Catalog

Каталог плагинов и интерфейсных расширений для [Hermes Desktop](https://github.com/NousResearch/hermes-agent).

Каждый модуль изолирован в своей папке внутри `plugins/<имя-плагина>` со своей собственной инструкцией, файлами и скриптами установки.

---

## 🌟 Доступные плагины в каталоге

| Плагин | Описание | Инструкция и файлы |
| :--- | :--- | :--- |
| ☆ **`favorites-models`** | Компактная кнопка быстрого выбора избранных моделей в шапке чата | [👉 Перейти к плагину](plugins/favorites-models/README.md) |
| ☆ **`antigravity-oauth`** | Прямой Google Cloud Code / Antigravity OAuth провайдер (Gemini) без сторонних утилит | [👉 Перейти к плагину](plugins/antigravity-oauth/README.md) |

*(Каталог пополняется новыми плагинами)*

---

## 📁 Структура каталога

```text
Hermes/
├── plugins/
│   ├── favorites-models/       # ☆ Плагин «Избранные модели»
│   │   ├── plugin.js
│   │   └── README.md
│   │
│   └── antigravity-oauth/      # ☆ Плагин «Google Antigravity OAuth»
│       ├── plugin.yaml
│       ├── __init__.py
│       ├── direct.py
│       ├── wire.mjs
│       ├── package.json
│       ├── install.bat
│       ├── install.sh
│       └── README.md
│
├── interface/                  # Патчи и мосты для Desktop интерфейса
├── docs/                       # Скриншоты и общая документация
├── install.py                  # Установщик Desktop-мостов
└── README.md
```

---

## 🚀 Быстрый старт на новом ПК

1. **Склонируйте репозиторий на свой компьютер:**
   ```bash
   git clone https://github.com/rusanoff1983-del/Hermes.git
   cd Hermes
   ```

2. **Выберите и установите нужный плагин:**

   - **☆ Кнопка «Избранные модели»:**
     Дважды кликните по **`install.bat`** (или выполните команду `python install.py --install-deps`), затем перезагрузите окно в Hermes (`Ctrl+K` → «Перезагрузить окно»). Подробнее: [инструкция к плагину](plugins/favorites-models/README.md).

   - **☆ Авторизация «Google Antigravity OAuth»:**
     Запустите **`install.bat`** внутри папки `plugins/antigravity-oauth` и выполните авторизацию в терминале:
     ```bash
     hermes auth add antigravity-direct
     ```
     Подробнее: [инструкция к плагину](plugins/antigravity-oauth/README.md).

---

## 🛡 Безопасность

- Репозиторий **не содержит** персональных токенов, ключей доступа или настроек пользователей.
- Все учетные данные шифруются локально на машине пользователя.

