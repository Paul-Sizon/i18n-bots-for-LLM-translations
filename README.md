# 🌍 i18n script bots

Python bots to internationalize and translate React (Next.js + TypeScript) apps powered by next-intl, with GPT-based AI.

### Pre-requisites

Integrate next-intl into your app. Follow the [next-intl documentation](https://next-intl.dev/) for setup.

## 🚀 Scripts Overview

### 1. `i18n-bot.py` – Auto-Wrap and Extract Keys

Scans `.tsx/.jsx` files in `app/` and `components/`, wraps visible text in `t()`, and extracts translation keys.

```bash
python i18n-bot.py
```

✅ Output:
- Overwrites `.tsx`/`.jsx` files with `t("...")`
- Updates `messages/en.json` with extracted keys

---

### 2. `translate.py` – Translate `en.json` to All Languages

Uses OpenAI to translate your keys

Edit the target languages in the script if needed:
```python
LANGUAGES_TO_TRANSLATE = ["es", "fr", "zh-CN", "tr", "es-AR"]
```

Run:
```bash
python translate.py
```

✅ Output:
- Creates/updates `messages/{lang}.json` files for each language

---

### 3. `translation_sync.py` – Sync Only New or Updated Keys

Only translates:
- 🆕 **New keys** added to `en.json`
- ✏️ Keys **marked for update** like this:

```json
{
  "welcome": {
    "update": "Welcome back!",    
  }
}
```

After running, `en.json` is cleaned up to:
```json
{
  "welcome": "Welcome back!"
}
```

Run:
```bash
python translation_sync.py
```

---

### 4. `translation_checker.py` – QA Translations with OpenAI

Automatically fixes problematic keys and logs any parse errors. Perhaps, it's better to use another LLM for this

Run:
```bash
python translation_checker.py
```

---

## 🧪 Example Workflow

```bash
# 1. Wrap UI strings and extract to en.json
python i18n-bot.py

# 2. Translate into all languages
python translate.py

# 3. Update only new or flagged keys
python translation_sync.py

# 4. Run QA on existing translations
python translation_checker.py
```

---

## 🌐 Supported Languages

Any language that GPT knows

---

⚠️ Note: These tools are optimized for use with the next-intl library.
Due to how next-intl works with static site generation (SSG) and dynamic imports, some manual refactoring may be required
