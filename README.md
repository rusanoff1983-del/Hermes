# Hermes — личный монорепозиторий расширений

Расширения для [Hermes Agent](https://github.com/NousResearch/hermes-agent), а не копия всего Hermes.

```text
Hermes/
├── plugins/favorites-models/plugin.js
├── interface/native-model-selection.patch
├── docs/
├── tests/
├── install.py
└── README.md
```

## Что устанавливается

**☆ Избранные модели** — кнопка перед штатным выбором модели, без надписи. Избранное выбирается только из явно настроенных у тебя провайдеров. Группы сворачиваются; переключатель скрывает каталог. Выбор и состояние меню сохраняются локально. Для нового и существующего чата используется штатный механизм выбора модели, а не запись в настройки всего профиля.

Плагину требуется небольшой мост `host.models.select` в интерфейсе Hermes. Установщик ставит **и мост, и плагин**, проверяет совместимость, запускает тесты и собирает интерфейс.

## Установка на другом ПК — три команды

Сначала установи Hermes **из исходников/git с Desktop**, Git, Python 3.10+ и Node.js 22.22+ / 24.11+ (с npm). Настрой свои провайдеры в Hermes. В Windows подходит установка с исходниками в `%LOCALAPPDATA%\hermes\hermes-agent`.

```sh
git clone https://github.com/rusanoff1983-del/Hermes.git
cd Hermes
python install.py --install-deps
```

В Linux/macOS, если команда Python называется `python3`, используй `python3 install.py --install-deps`.

Если npm-зависимости Hermes уже установлены, достаточно `python install.py`.

Установщик автоматически использует `$HERMES_HOME`; иначе Windows — `%LOCALAPPDATA%/hermes`, Linux/macOS — `~/.hermes`.

### Явные пути

```sh
python install.py --hermes-home "D:/HermesHome" --source "D:/src/hermes-agent" --install-deps
```

### Сначала проверить, не изменяя файлы

```sh
python install.py --check
```

### После установки

- Windows `release/win-unpacked`: установщик обновляет распакованный интерфейс. Перезагрузи окно через палитру команд (`Ctrl+K` → «Перезагрузить окно»).
- Если распакованная Windows-сборка не найдена: собран `apps/desktop/dist`. Запусти **именно эту** сборку: `cd <исходники-Hermes>/apps/desktop` и `npm exec electron .`.
- Произвольную установленную MSIX/AppImage/macOS `.app` установщик **не перепаковывает**. Для них используй исходную сборку или отдельно укажи корректный `--renderer-dir`. Подробнее: [установка](docs/installation.md).

## Безопасность и совместимость

- API-ключи, OAuth, `.env`, `auth.json`, `config.yaml`, переписки и личное избранное **не переносятся и не публикуются**.
- На другом ПК провайдеры подключаются отдельно; установка расширения не выдаёт доступ к аккаунтам.
- Исходники Hermes не переключаются на другую ветку и не сбрасываются.
- Перед правкой `git apply --check` проверяет совместимость. При конфликте установщик отказывается менять интерфейс.
- Проверенная ревизия upstream записана в `interface/compatibility.json`. Другие ревизии допустимы только если патч применим, тесты и сборка проходят; совместимость со всеми будущими версиями не обещается.
- Перед изменениями создаётся резервная копия с `receipt.json`. Существующие хешированные chunks не удаляются, чтобы не ломать уже открытое окно.
- После обновления самого Hermes мост может потребовать повторной установки/адаптации. Плагин живёт в пользовательской папке, но мост меняет исходники; эти изменения могут мешать `hermes update`.

## Откат

Путь к записи установки печатается в конце. Команда:

```sh
python install.py --rollback "<путь-к-backups>/<установка>/receipt.json"
```

Откат откажется затирать файлы, изменённые после установки. Настройки, ключи и чаты не затрагиваются.

## Тесты

```sh
python -m unittest discover -s tests -p "test_*.py" -v
```

Для проверки реального React/Radix плагина с зависимостями исходного Hermes:

```sh
# Git Bash/Linux/macOS
HERMES_SOURCE="/path/to/hermes-agent" node tests/plugin-regression.cjs plugins/favorites-models/plugin.js
```

PowerShell: `$env:HERMES_SOURCE="C:/path/to/hermes-agent"`, затем та же команда `node ...`.

Установщик дополнительно запускает тесты native bridge и штатного выбора модели, TypeScript-проверку и настоящую сборку Desktop.

## Добавление новых расширений

Отдельный каталог на каждое расширение в `plugins/`; изменения общего интерфейса — в `interface/`; инструкции — в `docs/`. Сейчас установщик устанавливает только `favorites-models`. Новые плагины не копируются автоматически без добавления их в установщик.

Исходный Hermes и затронутые upstream-файлы принадлежат Nous Research и участникам проекта. См. [лицензию upstream](https://github.com/NousResearch/hermes-agent/blob/main/LICENSE).
