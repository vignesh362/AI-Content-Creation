import requests
import time
import os

# CONFIGURATION
SCRIPT_FILE = "script.txt"
LLM_API_URL = "http://127.0.0.1:1234/v1/chat/completions"
MODEL_NAME = "llama-3.2-3b-instruct"

def load_script(script_file):
    """
    Loads the script from a text file.
    Expects each non-empty line to have the format: Speaker: Line
    """
    with open(script_file, "r") as f:
        script_lines = [line.strip() for line in f if line.strip()]
    parsed_script = []
    for line in script_lines:
        if ":" in line:
            speaker, content = line.split(":", 1)
            parsed_script.append((speaker.strip(), content.strip()))
    return parsed_script

def get_side_suggestions(line):
    """
    Calls the LLM to generate three creative suggestions, ideas, or product recommendations
    related to the provided line.
    """
    prompt = f"""
You are a creative assistant. Given the following line from a scripted conversation:
"{line}"
Provide three creative suggestions, ideas, or product recommendations related to the content of this line.
Format your response as bullet points.
"""
    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.5,
        "max_tokens": 150
    }
    try:
        response = requests.post(LLM_API_URL, json=payload)
        suggestions = response.json()["choices"][0]["message"]["content"].strip()
        return suggestions
    except Exception as e:
        return f"[LLM Error] {e}"

def display_script_with_highlight(parsed_script, current_index):
    """
    Clears the terminal and displays the entire script.
    The current line (at index current_index) is highlighted with a marker.
    """
    os.system('cls' if os.name == 'nt' else 'clear')
    print("🎬 Script Overview (current line highlighted):\n")
    for i, (speaker, line) in enumerate(parsed_script):
        if i == current_index:
            print(f">>> {speaker}: {line}")
        else:
            print(f"    {speaker}: {line}")
    print("\n" + "-"*50 + "\n")

def main():
    parsed_script = load_script(SCRIPT_FILE)
    total_lines = len(parsed_script)
    current_index = 0

    # Pre-fetch suggestion for the second line (if available)
    suggestion_for_current_line = None
    next_suggestion = None
    if total_lines > 1:
        next_suggestion = get_side_suggestions(parsed_script[1][1])

    while current_index < total_lines:
        display_script_with_highlight(parsed_script, current_index)

        speaker, line = parsed_script[current_index]
        print(f"💬 Current line: {speaker}: {line}\n")

        # For the first line, do not show any suggestion.
        if current_index == 0:
            print("💡 No suggestions for the first line.\n")
        else:
            print("💡 Suggestions for this line:")
            print(suggestion_for_current_line)
            print()

        print("-" * 50 + "\n")

        # Wait until the user presses exactly the space bar (and Enter).
        while True:
            user_input = input("Press the space bar (and Enter) to move to the next line: ")
            if user_input == " ":
                break
            else:
                print("Please press only the space bar followed by Enter to continue.")

        current_index += 1

        # Now, the suggestion pre-fetched for the next line becomes the current suggestion.
        suggestion_for_current_line = next_suggestion
        # Pre-fetch suggestion for the line after the new current line, if available.
        if current_index + 1 < total_lines:
            next_suggestion = get_side_suggestions(parsed_script[current_index + 1][1])
        else:
            next_suggestion = None

        time.sleep(0.5)

    print("🎬 End of script reached.")

if __name__ == "__main__":
    main()