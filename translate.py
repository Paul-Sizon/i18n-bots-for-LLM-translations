"""
📚 Translation Bot – Powered by OpenAI 🌍
----------------------------------------

This script translates your `translation.json` UI strings into multiple languages
using the OpenAI API.

📦 1. Install Dependencies
Run this in your terminal:
    python3 -m venv .venv
    source .venv/bin/activate
    pip install openai tqdm

🔑 2. Set Your OpenAI API Key
Export your key as an environment variable:
    export OPENAI_API_KEY=your-api-key-here

📁 3. Input & Output Paths
The script reads:
    messages/<language>.json

It outputs translated JSON files to:
    messages/<language>.json

🌐 4. Define Your Target Languages
Edit the `LANGUAGES_TO_TRANSLATE` list:
    LANGUAGES_TO_TRANSLATE = ["thai", "ukranian"]

🧩 5. Chunk Size
Translation is done in chunks (default: 50 key-value pairs). You can adjust:
    CHUNK_SIZE = 50

🚀 6. Run the Script
In the root of your project (where this script lives), run:
    python translate.py
"""

import os
import json
from openai import OpenAI
from tqdm import tqdm

# ============================== #
#        CONFIGURATION 🔧        #
# ============================== #

# API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise EnvironmentError("Please set your OPENAI_API_KEY environment variable.")
client = OpenAI(api_key=OPENAI_API_KEY)

# System Prompt Template
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

# Paths and Settings
INPUT_FILE_PATH = "messages/en.json"
OUTPUT_FOLDER = "messages"
MODEL = "gpt-4.1-nano"
CHUNK_SIZE = 36
LANGUAGES_TO_TRANSLATE = [
    # Major Global Languages
    "es",  # Spanish
    "ru",  # Russian
    "fr",  # French
    "de",  # German
    "it",  # Italian
    "pt",  # Portuguese
    "zh-CN",  # Chinese (Simplified)
    "zh-TW",  # Chinese (Traditional)
    "zh-HK",  # Chinese (Hong Kong)
    "ja",  # Japanese
    "ko",  # Korean

    # Web3 High-Activity Regions

    "tr",  # Turkish
    "vi",  # Vietnamese
    "uk",  # Ukrainian
    "fil",  # Filipino (Tagalog)
    "id",  # Indonesian
    "th",  # Thai
    "hi",  # Hindi
    "ur",  # Urdu
    "bn",  # Bengali
    "fa",  # Persian (Farsi)
    "ar",  # Arabic
    "he",  # Hebrew

    # South Asian Languages

    "ta",  # Tamil
    "te",  # Telugu
    "ml",  # Malayalam
    "kn",  # Kannada
    "mr",  # Marathi
    "gu",  # Gujarati
    "pa",  # Punjabi
    "ne",  # Nepali

    # Caucasus & Central Asia

    "hy",  # Armenian
    "ka",  # Georgian
    "kk",  # Kazakh
    "az",  # Azerbaijani

    # Balkan Languages

    "sr",  # Serbian
    "bs",  # Bosnian
    "mk",  # Macedonian
    "sq",  # Albanian

    # Extended European Languages

    "nl",  # Dutch
    "pl",  # Polish
    "sv",  # Swedish
    "no",  # Norwegian
    "da",  # Danish
    "fi",  # Finnish
    "cs",  # Czech
    "ro",  # Romanian
    "hu",  # Hungarian
    "el",  # Greek
    "bg",  # Bulgarian
    "hr",  # Croatian
    "sk",  # Slovak
    "sl",  # Slovenian
    "lt",  # Lithuanian
    "lv",  # Latvian
    "et",  # Estonian

    # Africa & Localized English

    "sw",  # Swahili
    "am",  # Amharic
    "ha",  # Hausa
    "en-NG",  # English (Nigeria)

    # Bonus Crypto/Regional

    "km",  # Khmer
    "my",  # Burmese
    "lo",  # Lao

    # Spanish Variants

    "es-MX",  # Mexico (~125M)
    "es-AR",  # Argentina (~45M)
    "es-US",  # United States (~42M)
    "es-CO",  # Colombia (~52M)
    "es-ES",  # Spain (~47M)
    "es-PE",  # Peru (~34M)
    "es-VE",  # Venezuela (~32M)
    "es-CL",  # Chile (~20M)
    "es-EC",  # Ecuador (~17M)
    "es-GT",  # Guatemala (~14M)
    "es-CU",  # Cuba (~11M)
    "es-BO",  # Bolivia (~11M)
    "es-DO",  # Dominican Republic (~10M)
    "es-HN",  # Honduras (~9M)
    "es-PY",  # Paraguay (~7M)
    "es-NI",  # Nicaragua (~6.5M)
    "es-SV",  # El Salvador (~6.5M)
    "es-CR",  # Costa Rica (~5M)
    "es-PA",  # Panama (~4.5M)
    "es-UY",  # Uruguay (~3.5M)
    "es-PR",  # Puerto Rico (~3M)
    "es-419",  # Latin America & Caribbean (catch-all, ~450M)
]


# ============================== #
#       TRANSLATION LOGIC 🧠      #
# ============================== #

def chunk_dict(data: dict, chunk_size: int):
    items = list(data.items())
    for i in range(0, len(items), chunk_size):
        yield dict(items[i : i + chunk_size])


def translate_chunk(chunk: dict, target_language: str) -> dict:
    print(f"🧠 Translating chunk into {target_language}...")

    system_message = SYSTEM_PROMPT.replace("{{target_language}}", target_language)
    chunk_str = json.dumps(chunk, ensure_ascii=False, indent=2)

    messages = [
        {"role": "system", "content": system_message},
        {
            "role": "user",
            "content": f"Here is the JSON content to translate:\n\n{chunk_str}",
        },
    ]

    response = client.chat.completions.create(
        model=MODEL, messages=messages, temperature=0.4
    )

    content = response.choices[0].message.content.strip()

    # Remove markdown formatting if returned
    if content.startswith("```json"):
        content = content.lstrip("```json").strip()
    elif content.startswith("```"):
        content = content.lstrip("```").strip()
    if content.endswith("```"):
        content = content.rstrip("```").strip()

    try:
        translated_chunk = json.loads(content)
        print(f"✅ Chunk translated successfully!")
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error while translating a chunk: {e}")
        print(f"⚠️ Raw content was:\n{content}")
        raise ValueError(f"Failed to decode JSON from API response: {e}")

    return translated_chunk


def translate_file(
    input_file: str,
    output_base_folder: str,
    target_languages: list,
    chunk_size: int = 50,
) -> None:
    print("📂 Loading English translation file...")
    with open(input_file, "r", encoding="utf-8") as f:
        original_data = json.load(f)
    print("✅ English file loaded!")

    os.makedirs(output_base_folder, exist_ok=True)

    for lang in target_languages:
        print(f"\n🌍 Starting translation for: {lang}")
        translated_data = {}
        chunks = list(chunk_dict(original_data, chunk_size))

        out_file = os.path.join(output_base_folder, f"{lang}.json")
        temp_file = os.path.join(output_base_folder, f"{lang}.temp.json")

        for idx, chunk in enumerate(
            tqdm(chunks, desc=f"🔄 Translating chunks for {lang}")
        ):
            try:
                translated_chunk = translate_chunk(chunk, lang)
                translated_data.update(translated_chunk)

                with open(temp_file, "w", encoding="utf-8") as tf:
                    json.dump(translated_data, tf, ensure_ascii=False, indent=2)

            except Exception as e:
                print(f"⚠️ Skipping chunk {idx + 1}/{len(chunks)} due to error: {e}")
                with open(
                    os.path.join(output_base_folder, f"{lang}_error_chunk_{idx+1}.log"),
                    "w",
                    encoding="utf-8",
                ) as ef:
                    ef.write(str(e))
                continue

        if translated_data:
            with open(out_file, "w", encoding="utf-8") as outf:
                json.dump(translated_data, outf, ensure_ascii=False, indent=2)
            print(f"📁 Translation for '{lang}' saved to {out_file} 🚀")

            if os.path.exists(temp_file):
                os.remove(temp_file)
                print(f"🗑️ Temporary file '{temp_file}' removed.")
        else:
            print(
                f"❌ No translation data was saved for '{lang}'. Something went wrong."
            )


# ============================== #
#             MAIN 🚀            #
# ============================== #

if __name__ == "__main__":
    print("🔧 Starting translation process...")
    translate_file(INPUT_FILE_PATH, OUTPUT_FOLDER, LANGUAGES_TO_TRANSLATE, CHUNK_SIZE)
    print("\n🎉 All done! Your translations are ready.")
