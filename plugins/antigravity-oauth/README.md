<p align="center">
  <a href="README.ru.md">
    <img src="https://img.shields.io/badge/Язык-🇷🇺%20Русский-blue?style=for-the-badge" alt="Русский">
  </a>
  &nbsp;&nbsp;
  <a href="README.md">
    <img src="https://img.shields.io/badge/Language-🇬🇧%20English-2ea44f?style=for-the-badge" alt="English">
  </a>
</p>

# ⚡ Google Antigravity OAuth Plugin (Gemini)

Direct Google Cloud Code / Antigravity model provider for **Hermes Agent**.

Provides direct access to Gemini models (Gemini 3.8 / 3.7 / 3.6 / 3.5 Flash and Pro) via secure 1-click Google OAuth in browser — without third-party CLI tools or manual token copying.

---

## 📦 Quick Installation on Your PC

### Option 1. Simplest (1-Click on Windows)
1. Download this repository (click **`Code`** at the top → **`Download ZIP`**) and extract it.
2. Open `plugins/antigravity-oauth` and double-click **`install.bat`**.
3. The script will automatically copy the plugin, install dependencies, and open your browser to log into Google.

---

### Option 2. Terminal (Copy & Paste)
```bash
git clone https://github.com/rusanoff1983-del/Hermes.git
cd Hermes/plugins/antigravity-oauth
install.bat
```

---

## 🔑 Step 2. Google Authentication

> ⚠️ **Important:** Do NOT type this command into your browser address bar! Enter it into your terminal / command prompt (`cmd`). The browser will open automatically.

### How to Authenticate:

1. Open Windows Command Prompt (**`Win + R`** → type **`cmd`** → press **Enter**).
2. Paste this command and press **Enter**:
   ```bash
   hermes auth add antigravity-direct
   ```
3. **What happens next:**
   - The command automatically opens your default browser with a standard Google login page.
   - Choose your Google account and click **"Allow"**.
   - In your command prompt, you will see `Connected`. Done!

---

## 🛠 Useful Terminal Commands (`cmd`):

- **Check connection status:**
  ```bash
  hermes auth status antigravity-direct
  ```

- **Log out (remove stored credentials):**
  ```bash
  hermes auth logout antigravity-direct
  ```

---

## 🚀 Usage

### Run a chat in terminal:
```bash
hermes chat --provider antigravity-direct -m gemini-3.7-flash-medium
```

### Set as default provider:
In your Hermes profile `config.yaml`:
```yaml
model:
  default: "gemini-3.7-flash-medium"
  provider: "antigravity-direct"
```

---

## 📋 Available Models

- `gemini-3.8-flash-high`, `gemini-3.8-flash-medium`, `gemini-3.8-flash-low`
- `gemini-3.7-flash-high`, `gemini-3.7-flash-medium`, `gemini-3.7-flash-low`
- `gemini-3.6-flash-high`, `gemini-3.6-flash-medium`, `gemini-3.6-flash-low`
- `gemini-3.5-flash-high`, `gemini-3.5-flash-medium`, `gemini-3.5-flash-low`
- `gemini-3.1-pro-high`, `gemini-3.1-pro-low`

---

## 🛡️ Security & Privacy

- This repository **never contains** private tokens, keys, or credentials.
- Each user authenticates independently via their own Google account.
- Tokens are encrypted locally on your machine using Windows DPAPI (`credential.dpapi`).
