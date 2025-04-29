"""
=========================================
🧪 TRANSLATION QUALITY CHECKER BOT 🧪
=========================================

🔍 WHAT IT DOES:
- Compares translations in `{lang}.json` files against the source `en.json`.
- Checks for accuracy, naturalness, tone, and cultural relevance.
- Automatically corrects problematic translations.
- Logs unparseable LLM responses to `{lang}_parse_error.log`.

⚙️ HOW TO USE:
1. Install dependencies:
   pip install openai tqdm

2. Set your OpenAI API key:
   export OPENAI_API_KEY="your-api-key"

3. Run the script:
   python translation_check.py

   - It will auto-detect all target language JSON files in the `messages/` folder.

⚠️ NOTE:
- Only problematic translations are corrected.
- If a translation is acceptable, it is left untouched.
- Parsing issues from OpenAI's response are logged and skipped to avoid data loss.

"""

import os
import json
from openai import OpenAI
from tqdm import tqdm
import re

# ============================== #
#         CONFIGURATION         #
# ============================== #

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise EnvironmentError("Please set your OPENAI_API_KEY environment variable.")
client = OpenAI(api_key=OPENAI_API_KEY)

INPUT_FILE_PATH = "messages/en.json"
TRANSLATION_FOLDER = "messages"
MODEL = "gpt-4.1"

# Detect available languages automatically
LANGUAGES_TO_CHECK = [
    f[:-5] for f in os.listdir(TRANSLATION_FOLDER)
    if f.endswith(".json") and f != "en.json"
]

SYSTEM_PROMPT = """
You are a professional localization QA specialist, working in venturo studio that builds web3 dapps. Your task is to review translations of UI text.

Here is what to check:

1. **Accuracy**: Does the translation reflect the correct meaning of the original English string?
2. **Naturalness**: Does the translation sound fluent and natural in the target language?
3. **Tone**: Is the tone appropriate for a user interface? Avoid cringy, overly formal or robotic tones.
4. **Cultural relevance**: Is any slang or idiomatic expression localized correctly?

Only return a JSON object of problematic entries in the form:
{
  "key": {
    "translation": "corrected translation",
    "issue": "short explanation"
  }
}
If everything looks good, return an empty object.
"""

def clean_quotes_and_escape(content: str) -> str:
    # Replace curly quotes
    content = (
        content.replace("“", "\"").replace("”", "\"")
               .replace("‘", "'").replace("’", "'")
               .replace("«", "\"").replace("»", "\"")
    )
    # Escape unescaped inner quotes in `translation` or `issue` fields
    def escape_inner_quotes(match):
        return match.group(0).replace('"', '\\"')
    
    # Match values inside "translation": "..." or "issue": "..."
    pattern = r'(?<="translation":\\s?)"(.*?[^\\])"|(?<="issue":\\s?)"(.*?[^\\])"'
    return re.sub(pattern, lambda m: f"\"{escape_inner_quotes(m)}\"", content)

def check_translation_chunk(en_chunk: dict, translated_chunk: dict, target_language: str) -> dict:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Check the following translations from English to '{target_language}':\n\nENGLISH:\n{json.dumps(en_chunk, ensure_ascii=False, indent=2)}\n\nTRANSLATED:\n{json.dumps(translated_chunk, ensure_ascii=False, indent=2)}"}
    ]

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0.3
    )

    content = response.choices[0].message.content.strip()

    # Remove Markdown fences
    if content.startswith("```json"):
        content = content[len("```json"):].strip()
    elif content.startswith("```"):
        content = content[len("```"):].strip()
    if content.endswith("```"):
        content = content[:-3].strip()

    content = clean_quotes_and_escape(content)

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        # Fallback: try extracting JSON from the mess
        json_match = re.search(r'{.*}', content, re.DOTALL)
        if json_match:
            raw = clean_quotes_and_escape(json_match.group(0))
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                pass

        log_path = os.path.join(TRANSLATION_FOLDER, f"{target_language}_parse_error.log")
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"⚠️ Could not parse JSON response for '{target_language}' — logged to {log_path}")
        return {"error": content}

def chunk_dict(data: dict, chunk_size: int):
    items = list(data.items())
    for i in range(0, len(items), chunk_size):
        yield dict(items[i:i + chunk_size])

def check_translations(input_file: str, folder: str, languages: list, chunk_size: int = 36):
    print("📂 Loading English source...")
    with open(input_file, 'r', encoding='utf-8') as f:
        en_data = json.load(f)

    for lang in languages:
        lang_file = os.path.join(folder, f"{lang}.json")
        if not os.path.exists(lang_file):
            print(f"❌ {lang_file} not found. Skipping.")
            continue

        print(f"🔍 Checking translations for: {lang}")
        with open(lang_file, 'r', encoding='utf-8') as f:
            translated_data = json.load(f)

        problems = {}

        for chunk in tqdm(list(chunk_dict(en_data, chunk_size)), desc=f"Checking {lang}"):
            translated_chunk = {k: translated_data.get(k, "") for k in chunk.keys()}
            issues = check_translation_chunk(chunk, translated_chunk, lang)
            problems.update(issues)

        if problems:
            for key, data in problems.items():
                if isinstance(data, dict) and "translation" in data:
                    translated_data[key] = data["translation"]
            with open(lang_file, 'w', encoding='utf-8') as f:
                json.dump(translated_data, f, ensure_ascii=False, indent=2)
            print(f"✏️ Updated translations written to {lang_file}")
        else:
            print(f"✅ No issues found in {lang}")

if __name__ == "__main__":
    print("🔧 Running Translation Checker Bot...")
    check_translations(INPUT_FILE_PATH, TRANSLATION_FOLDER, LANGUAGES_TO_CHECK)
    print("\n🎉 Translation checks and updates complete!")