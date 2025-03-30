import re
import json

def format_json(input_str: str) -> str:
    json_blocks = re.findall(r'\[\s*{.*?}\s*\]', input_str, re.DOTALL)
    combined_dialogs = []
    formatted_str = ''

    for block in json_blocks:
        try:
            parsed = json.loads(block)
            combined_dialogs.extend(parsed)
        except Exception as e:
            print(f"Skipped malformed block: {e}")

    for pair in combined_dialogs:
        for speaker, line in pair.items():
            formatted_str += f"{speaker}: {line}\n\n"

    return formatted_str
