import os
import time
from pathlib import Path

# NOTE: You need to install deep-translator to use this script.
# Run: pip install deep-translator

try:
    from deep_translator import GoogleTranslator
except ImportError:
    print("Error: The 'deep-translator' library is not installed.")
    print("Please install it by running: pip install deep-translator")
    exit(1)

DOCS_DIR = Path(__file__).parent
BASE_README = DOCS_DIR / "README.md"

TARGETS = {
    "ko": {
        "file": "README.ko.md",
        "language": "Korean"
    },
    "ja": {
        "file": "README.ja.md",
        "language": "Japanese"
    },
    "zh-CN": {
        "file": "README.zh.md",
        "language": "Chinese (Simplified)"
    }
}

def translate_readme():
    if not BASE_README.exists():
        print(f"Error: {BASE_README.name} not found!")
        exit(1)
        
    print(f"Reading {BASE_README.name}...")
    source_content = BASE_README.read_text(encoding="utf-8")
    
    # deep-translator has a 5000 character limit per request.
    # We must split the markdown file into chunks (e.g., by lines or blocks).
    # This is a simple line-by-line or paragraph chunker.
    
    paragraphs = source_content.split('\n\n')
    
    for lang_code, target_info in TARGETS.items():
        lang_name = target_info["language"]
        target_file = DOCS_DIR / target_info["file"]
        
        print(f"\nTranslating to {lang_name} ({lang_code})...")
        translator = GoogleTranslator(source='auto', target=lang_code)
        
        translated_paragraphs = []
        
        # Translate paragraph by paragraph to avoid 5000 char limit
        # and to preserve basic markdown block structure.
        for i, p in enumerate(paragraphs):
            # Skip empty paragraphs or pure code blocks if possible, 
            # though Google Translate might mangle code blocks anyway.
            if not p.strip():
                translated_paragraphs.append("")
                continue
            
            # Simple heuristic to avoid translating code blocks
            if p.startswith("```"):
                translated_paragraphs.append(p)
                continue
                
            try:
                # Add a small delay to avoid hitting rate limits
                time.sleep(0.5)
                translated = translator.translate(p)
                translated_paragraphs.append(translated if translated else p)
            except Exception as e:
                print(f"Error translating chunk {i}: {e}")
                translated_paragraphs.append(p) # Fallback to original
        
        translated_content = '\n\n'.join(translated_paragraphs) + "\n"
        target_file.write_text(translated_content, encoding="utf-8")
        print(f"✅ Successfully updated {target_file.name}")

if __name__ == "__main__":
    translate_readme()
    print("\nAll translations finished!")
