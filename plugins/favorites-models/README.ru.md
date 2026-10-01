<div align="right">
  <a href="README.ru.md">🇷🇺 <b>Русский</b></a> &nbsp;|&nbsp;
  <a href="README.md">🇬🇧 English</a>
</div>

# ⭐ Плагин «Избранные модели» для Hermes Desktop

Интерфейсный плагин для [Hermes Desktop](https://github.com/NousResearch/hermes-agent), добавляющий компактную кнопку быстрого выбора избранных моделей прямо в шапку чата.

---

## ✨ Возможности

- **Компактная кнопка «☆»** в шапке чата перед стандартным выбором модели.
- **Умное меню**: показывает только модели из реально настроенных провайдеров.
- **Группировка**: аккуратное сворачивание списков по провайдерам.
- **Штатный выбор**: использует мост `host.models.select`, корректно переключая модель для текущего или нового чата.
- **Локальное сохранение**: избранное хранится локально на вашем компьютере.

---

## 📦 Как установить на своём ПК

### Вариант 1. Самый простой (в 1 клик мышкой)
1. Скачайте репозиторий (кнопка **`Code`** вверху страницы → **`Download ZIP`**) и распакуйте.
2. В папке `plugins/favorites-models` (или в корне) дважды кликните по файлу **`install.bat`**.
3. В Hermes Desktop нажмите `Ctrl+K` → **«Перезагрузить окно»**.

---

### Вариант 2. Через терминал (скопировать и вставить)
```bash
git clone https://github.com/rusanoff1983-del/Hermes.git
cd Hermes/plugins/favorites-models
python install.py --install-deps
```
После завершения нажмите `Ctrl+K` в Hermes Desktop → **«Перезагрузить окно»**.

---

## 📁 Файлы плагина

- `plugin.js` — готовый скомпилированный плагин (React / Radix UI).
- `install.py` / `install.bat` — скрипты автоматической интеграции и сборки.
- `native-model-selection.patch` — патч для исходников Hermes Desktop.
- `models.ts` — TypeScript-исходник модуля выбора моделей.
- `models.test.ts` — юнит-тесты для TypeScript моста.
- `compatibility.json` — проверенные ревизии совместимости.

---

<details>
<summary><b>📸 Скриншоты интерфейса (нажмите, чтобы развернуть)</b></summary>

<br />

### Расположение кнопки в панели чата:
<p align="center">
  <img src="images/button-placement.png" alt="Расположение кнопки" width="90%" />
</p>

### Меню выбора избранных моделей:
<p align="center">
  <img src="images/favorites-menu-full.png" alt="Полное меню избранного" width="48%" />
  <img src="images/favorites-dropdown.png" alt="Компактное меню" width="48%" />
</p>

</details>
