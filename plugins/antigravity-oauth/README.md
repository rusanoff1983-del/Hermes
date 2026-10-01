# ☆ Google Antigravity OAuth Plugin (Gemini)

Прямой плагин провайдера моделей Google Cloud Code / Antigravity для **Hermes Agent**.

Позволяет использовать быстрые модели семейства Gemini (Gemini 3.8 / 3.7 / 3.6 / 3.5 Flash и Pro) напрямую через защищенный вход в Google в браузере — без сторонних утилит и без ручного переноса токенов.

---

## 📦 Быстрая установка на ПК

### Вариант 1. Самый простой (в 1 клик мышкой)
1. Скачайте репозиторий (кнопка **`Code`** вверху страницы → **`Download ZIP`**) и распакуйте архив.
2. Зайдите в папку `plugins/antigravity-oauth` и дважды кликните по файлу **`install.bat`**.
3. Скрипт сам скопирует плагин, установит зависимости и откроет браузер для входа в ваш Google-аккаунт.

---

### Вариант 2. Через терминал (скопировать и вставить)
```bash
git clone https://github.com/rusanoff1983-del/Hermes.git
cd Hermes/plugins/antigravity-oauth
install.bat
```

---

## 🔑 Управление авторизацией

- **Войти в аккаунт Google в браузере:**
  ```bash
  hermes auth add antigravity-direct
  ```
  *(В браузере откроется окно входа Google, подтвердите доступ).*

- **Проверить статус подключения:**
  ```bash
  hermes auth status antigravity-direct
  ```

- **Выйти из аккаунта:**
  ```bash
  hermes auth logout antigravity-direct
  ```

---

## 🚀 Использование

### Запуск чата в терминале:
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

## 🛡 Безопасность

- Репозиторий **не содержит** никаких персональных токенов, ключей или учетных данных.
- Каждый пользователь авторизуется самостоятельно через свой Google-аккаунт.
- Токены шифруются локально на компьютере через Windows DPAPI (`credential.dpapi`).
