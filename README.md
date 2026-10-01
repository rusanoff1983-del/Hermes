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

## 🚀 Быстрая установка на ПК

### Вариант 1. Самый простой (мышкой через браузер)
1. Нажмите зелёную кнопку **`Code`** вверху этой страницы → выберите **`Download ZIP`**.
2. Распакуйте скачанный архив в любое место.
3. Откройте папку и дважды кликните по **`install.bat`**.
4. В приложении Hermes Desktop нажмите `Ctrl+K` → **«Перезагрузить окно»**.

---

### Вариант 2. Через командную строку (через Git)
Скопируйте и вставьте команды в терминал:
```bash
git clone https://github.com/rusanoff1983-del/Hermes.git
cd Hermes
python install.py --install-deps
```
После завершения нажмите `Ctrl+K` в Hermes Desktop → **«Перезагрузить окно»**.

---

## 🛡 Безопасность

- Репозиторий **не содержит** персональных токенов, ключей доступа или настроек пользователей.
- Все учетные данные шифруются локально на машине пользователя.

