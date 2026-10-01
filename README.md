# Hermes Antigravity Direct Plugin

Прямой плагин провайдера моделей Google Cloud Code / Antigravity для **Hermes Agent**.

Позволяет использовать быстрые модели семейства Gemini (Gemini 3.8 / 3.7 / 3.6 / 3.5 Flash и Pro) напрямую через защищенный Google OAuth в браузере — без установки сторонних утилит и без ручного переноса токенов.

---

## ✨ Особенности

- 🌐 **Вход в браузере (OAuth 2.0 PKCE):** Авторизация в один клик через стандартную учетную запись Google.
- 🔒 **Безопасность (Windows DPAPI):** Токены шифруются ключом вашей локальной учетной записи Windows (`credential.dpapi`) и никогда не попадают в репозитории или открытые логи.
- ⚡ **Прямой сетевой шлюз:** Работает напрямую с `daily-cloudcode-pa.googleapis.com` через транспорт `@cortexkit/antigravity-auth-core` 2.2.0.
- 🛠 **Поддержка инструментов (Function Calling):** Поддерживает запуск инструментов Hermes Agent и передачу результатов.
- 🔤 **Чистая кодировка UTF-8:** Потоковое декодирование для корректной работы с кириллицей и русским языком.

---

## 📦 Быстрая установка

### Вариант 1. Установка в 1 клик (Windows)
1. Скачайте или клонируйте ветку репозитория:
   ```bash
   git clone -b antigravity-oauth https://github.com/rusanoff1983-del/Hermes.git antigravity-oauth
   cd antigravity-oauth
   ```
2. Запустите файл `install.bat`.
   Он автоматически скопирует плагин в папку Hermes и установит необходимые библиотеки Node.js.

---

### Вариант 2. Ручная установка (Любая ОС)
1. Скопируйте файлы плагина в каталог плагинов Hermes:
   - **Windows:** `%LOCALAPPDATA%\hermes\plugins\antigravity-direct`
   - **Linux / macOS:** `~/.hermes/plugins/antigravity-direct`
2. Перейдите в папку плагина и установите зависимости Node.js:
   ```bash
   cd ~/.hermes/plugins/antigravity-direct   # или %LOCALAPPDATA%\hermes\plugins\antigravity-direct
   npm install --no-audit --no-fund
   ```

---

## 🔑 Авторизация

Чтобы войти в свой аккаунт Google:

```bash
hermes auth add antigravity-direct
```

1. Автоматически откроется страница авторизации Google в браузере.
2. Подтвердите вход в свой аккаунт.
3. Токен будет безопасно зашифрован и сохранен на вашем ПК.

### Проверка статуса авторизации:
```bash
hermes auth status antigravity-direct
```

### Выход из учетной записи:
```bash
hermes auth logout antigravity-direct
```

---

## 🚀 Использование

### Запуск в командной строке:
```bash
hermes chat --provider antigravity-direct -m gemini-3.7-flash-medium
```

### Установка провайдером по умолчанию:
В файле `config.yaml` вашего профиля Hermes укажите:
```yaml
model:
  default: "gemini-3.7-flash-medium"
  provider: "antigravity-direct"
```

---

## 📋 Доступные модели

- `gemini-3.8-flash-high`, `gemini-3.8-flash-medium`, `gemini-3.8-flash-low`
- `gemini-3.7-flash-high`, `gemini-3.7-flash-medium`, `gemini-3.7-flash-low`
- `gemini-3.6-flash-high`, `gemini-3.6-flash-medium`, `gemini-3.6-flash-low`
- `gemini-3.5-flash-high`, `gemini-3.5-flash-medium`, `gemini-3.5-flash-low`
- `gemini-3.1-pro-high`, `gemini-3.1-pro-low`

---

## 🛡 Безопасность и конфиденциальность

- Репозиторий **не содержит** никаких персональных токенов, ключей доступа или учетных данных.
- Каждый пользователь авторизуется самостоятельно через свой Google-аккаунт.
- Токены хранятся исключительно локально на машине пользователя.

## 📄 Лицензия
MIT License.
