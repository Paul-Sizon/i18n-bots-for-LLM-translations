"""
===================================== 
🔁 HOW TRANSLATION SYNC WORKS 🔁
=====================================

✅ NEW KEYS:
- If a key is newly added to `en.json`, it will be automatically translated 
  into all other target language files (`{lang}.json`) the next time the script runs.

🔁 FORCE UPDATE EXISTING KEYS:
- To force re-translation of a specific key, wrap it in an object with `text` and `update: true`.
  For example:

  {
    "welcome": {
      "text": "Welcome back!",
      "update": true
    }
  }

- This tells the script to retranslate the "welcome" key, even if it already exists in the target files.
- After translation, the script will clean up the entry and convert it back to:

  {
    "welcome": "Welcome back!"
  }

This makes it easy to keep translations in sync as English source strings evolve.
"""



import os
import json
from openai import OpenAI
from tqdm import tqdm

# ============================== #
#        CONFIGURATION 🔧        #
# ============================== #

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise EnvironmentError("Please set your OPENAI_API_KEY environment variable.")
client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """You are a professional translator specializing in software localization for web3 dapps. Your task is to translate UI text and app content from English into the target language, identified by the IETF language code: {{target_language}}.

Follow these guidelines carefully:

1. **JSON Structure:**
    - **Keys:** Do not change any keys.
    - **Values:** Translate only the values.
    - **Output:** Return a properly formatted JSON object with the same keys as the input.

2. **Translation Quality:**
    - Prioritize natural, fluent, and context-appropriate translations that sound native to a speaker of the {{target_language}} locale.
    - Ensure that the translations sound native, clear, and non-cringy in a user interface setting.
    - Avoid overly formal or awkward wording unless the original tone calls for it.

3. **Placeholders and Variables:**
    - Preserve all placeholders (e.g., {name}, {amount}, %s) exactly as written.
    - Do not translate or alter variable formats.

4. **Error Correction:**
    - If the source English contains typos or awkward phrasing (e.g., "Elegible"), produce a corrected and natural-sounding translation.

5. **Localization Considerations:**
    - Adapt content naturally to the local language and culture where appropriate.
    - For example, for phrases like "Is it safe? Can I get rugged?", localize slang/context rather than translating literally.

6. **Language Code Awareness:**
    - The target language is passed in IETF format (e.g., "fr" for French, "zh-CN" for Simplified Chinese).
    - Use standard spelling and grammar conventions of that locale.
Translate to {{target_language}}
"""

INPUT_FILE_PATH = "messages/en.json"
OUTPUT_FOLDER = "messages"
MODEL = "gpt-4.1-nano"
CHUNK_SIZE = 36

LANGUAGES_TO_TRANSLATE = [
    lang[:-5] for lang in os.listdir(OUTPUT_FOLDER) if lang.endswith('.json') and lang != 'en.json'
]

# ============================== #
#       TRANSLATION LOGIC 🧠      #
# ============================== #

def chunk_dict(data: dict, chunk_size: int):
    items = list(data.items())
    for i in range(0, len(items), chunk_size):
        yield dict(items[i:i + chunk_size])

def translate_chunk(chunk: dict, target_language: str) -> dict:
    system_message = SYSTEM_PROMPT.replace("{{target_language}}", target_language)
    chunk_str = json.dumps(chunk, ensure_ascii=False, indent=2)
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": f"Here is the JSON content to translate:\n\n{chunk_str}"}
    ]

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0.4
    )

    content = response.choices[0].message.content.strip()
    if content.startswith("```json"):
        content = content.lstrip("```json").strip()
    elif content.startswith("```"):
        content = content.lstrip("```").strip()
    if content.endswith("```"):
        content = content.rstrip("```").strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in translation: {e}\n\n{content}")

def translate_sync(input_file: str, output_folder: str, target_languages: list, chunk_size: int = 50):
    print("📂 Loading source English file...")
    with open(input_file, 'r', encoding='utf-8') as f:
        en_data = json.load(f)

    updates = {k: v for k, v in en_data.items() if isinstance(v, dict) and v.get("update")}
    new_keys = {k: v for k, v in en_data.items() if k not in updates and not isinstance(v, dict)}

    print(f"🆕 {len(new_keys)} new keys | ✏️ {len(updates)} keys marked for update")

    for lang in target_languages:
        print(f"\n🌍 Syncing language: {lang}")
        out_path = os.path.join(output_folder, f"{lang}.json")

        if os.path.exists(out_path):
            with open(out_path, 'r', encoding='utf-8') as f:
                target_data = json.load(f)
        else:
            target_data = {}

        to_translate = {}

        for key, value in new_keys.items():
            if key not in target_data:
                to_translate[key] = value

        for key, update in updates.items():
            if key in en_data:
                to_translate[key] = update["text"] if isinstance(update, dict) else update

        if not to_translate:
            print("✅ No translation needed for this language.")
            continue

        translated_data = {}
        for chunk in tqdm(list(chunk_dict(to_translate, chunk_size)), desc=f"🔄 Translating {lang}"):
            try:
                result = translate_chunk(chunk, lang)
                translated_data.update(result)
            except Exception as e:
                print(f"❌ Error translating chunk: {e}")

        target_data.update(translated_data)
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(target_data, f, ensure_ascii=False, indent=2)
        print(f"📁 Synced: {lang}.json")

    # Clean up update markers in en.json
    for key in updates:
        if isinstance(en_data[key], dict):
            en_data[key] = updates[key]["text"] if "text" in updates[key] else updates[key]

    with open(input_file, 'w', encoding='utf-8') as f:
        json.dump(en_data, f, ensure_ascii=False, indent=2)
    print("🧹 Cleaned up update flags in en.json")        

# ============================== #
#             MAIN 🚀            #
# ============================== #

if __name__ == "__main__":
    print("🔧 Running Smart Translation Sync Bot...")
    translate_sync(INPUT_FILE_PATH, OUTPUT_FOLDER, LANGUAGES_TO_TRANSLATE, CHUNK_SIZE)
    print("\n✅ All languages synced!")
