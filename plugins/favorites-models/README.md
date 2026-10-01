<p align="center">
  <a href="README.ru.md">
    <img src="https://img.shields.io/badge/Язык-🇷🇺%20Русский-blue?style=for-the-badge" alt="Русский">
  </a>
  &nbsp;&nbsp;
  <a href="README.md">
    <img src="https://img.shields.io/badge/Language-🇬🇧%20English-2ea44f?style=for-the-badge" alt="English">
  </a>
</p>

# ⭐ Favorite Models Plugin for Hermes Desktop

UI plugin for [Hermes Desktop](https://github.com/NousResearch/hermes-agent) that adds a compact quick-select button for favorite models directly into the chat header.

---

## ✨ Features

- **Compact "☆" button** in the chat header right before the default model picker.
- **Smart menu**: dynamically displays models only from your configured providers.
- **Collapsible groups**: clean provider-based grouping and collapsible lists.
- **Native model selection**: uses the `host.models.select` bridge to cleanly switch active chat model without resetting user configs.
- **Local persistence**: your favorite models and menu states are saved locally on your machine.

---

## 📦 Installation on Your PC

### Option 1. Simplest (1-Click on Windows)
1. Download this repository (click **`Code`** at the top → **`Download ZIP`**) and extract it.
2. Inside `plugins/favorites-models` (or in the root folder), double-click **`install.bat`**.
3. In Hermes Desktop, press `Ctrl+K` → **"Reload Window"**.

---

### Option 2. Terminal (Copy & Paste)
```bash
git clone https://github.com/rusanoff1983-del/Hermes.git
cd Hermes/plugins/favorites-models
python install.py --install-deps
```
After completion, press `Ctrl+K` in Hermes Desktop → **"Reload Window"**.

---

## 📁 Plugin Files

- `plugin.js` — production-ready React / Radix UI plugin.
- `install.py` / `install.bat` — automated build and bridge installer scripts.
- `native-model-selection.patch` — SDK patch for Hermes Desktop source.
- `models.ts` — TypeScript model selection module source.
- `models.test.ts` — automated unit tests for TypeScript bridge.
- `compatibility.json` — verified upstream compatibility hashes.

---

<details>
<summary><b>📸 UI Screenshots (click to expand)</b></summary>

<br />

### Button placement in chat header:
<p align="center">
  <img src="images/button-placement.png" alt="Button Placement" width="90%" />
</p>

### Favorite models dropdown menu:
<p align="center">
  <img src="images/favorites-menu-full.png" alt="Full Favorites Menu" width="48%" />
  <img src="images/favorites-dropdown.png" alt="Compact Dropdown" width="48%" />
</p>

</details>
