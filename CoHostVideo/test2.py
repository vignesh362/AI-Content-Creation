import os
import time
import threading
import requests
import pygame
import cv2
import numpy as np
import textwrap
import asyncio
import edge_tts  # using edge-tts for natural TTS

# ---------- CONFIGURATION ----------
SCRIPT_FILE = "script.txt"
LLM_API_URL = "http://127.0.0.1:1234/v1/chat/completions"
MODEL_NAME = "llama-3.2-3b-instruct"

# Initial window sizes
VIDEO_WIDTH, VIDEO_HEIGHT = 640, 480
INIT_TRANSCRIPT_WIDTH, INIT_TRANSCRIPT_HEIGHT = 800, 800
FPS = 60

# Colors and style
BG_COLOR = (245, 245, 245)
BORDER_COLOR = (200, 200, 200)
HEADER_COLOR = (50, 50, 50)
TEXT_COLOR = (30, 30, 30)
BUTTON_COLOR = (100, 149, 237)
BUTTON_HOVER_COLOR = (65, 105, 225)
DIVIDER_COLOR = (180, 180, 180)

# ---------- ANIMATION STATES ----------
class AnimationState:
    ENTERING = 0
    TALKING = 1
    LEAVING = 2
    FINISHED = 3

# ---------- SCRIPT & SUGGESTION FUNCTIONS ----------
def load_script(script_file):
    with open(script_file, "r") as f:
        lines = [line.strip() for line in f if line.strip()]
    parsed_script = []
    for line in lines:
        if ":" in line:
            speaker, content = line.split(":", 1)
            parsed_script.append((speaker.strip(), content.strip()))
    return parsed_script

def get_side_suggestions(line):
    # The prompt now asks for creative variations.
    prompt = f"""
You are a creative assistant. Given the following line from a conversation:
"{line}"
Provide three creative variations, ideas, or product recommendations related to the content.
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
    except Exception as e:
        suggestions = f"[LLM Error] {e}"
    return suggestions

def fetch_suggestions_async(line, callback):
    def task():
        suggestion = get_side_suggestions(line)
        callback(suggestion)
    threading.Thread(target=task, daemon=True).start()

# ---------- ELF KING ANIMATION & IMAGE FUNCTIONS ----------
def load_frames_from_folder(folder_path, scale_factor):
    frames = []
    if not os.path.exists(folder_path):
        print(f"Folder not found: {folder_path}")
        return frames
    for file in sorted(os.listdir(folder_path)):
        if file.endswith('.png'):
            image = pygame.image.load(os.path.join(folder_path, file)).convert_alpha()
            scaled = pygame.transform.scale(
                image,
                (int(image.get_width() * scale_factor),
                 int(image.get_height() * scale_factor))
            )
            frames.append(scaled)
    return frames

class ElfKing(pygame.sprite.Sprite):
    def __init__(self, x, y, scale_factor=2.0):
        super().__init__()
        self.x = x
        self.y = y
        self.base_y = y
        self.state = "walk"
        self.frame_index = 0
        self.animations = {
            "Idle": load_frames_from_folder("extracted_elfking/Idle", scale_factor),
            "walk": load_frames_from_folder("extracted_elfking/walk", scale_factor)
        }
        if self.animations[self.state]:
            self.image = self.animations[self.state][0]
        else:
            self.image = pygame.Surface((50, 50), pygame.SRCALPHA)
            self.image.fill((0, 255, 0, 255))
        self.rect = self.image.get_rect(center=(x, y))
        self.last_update = pygame.time.get_ticks()
        self.direction = 1

    def update(self, animation_state):
        now = pygame.time.get_ticks()
        if self.animations[self.state] and now - self.last_update > 100:
            self.frame_index = (self.frame_index + 1) % len(self.animations[self.state])
            frame_img = self.animations[self.state][self.frame_index]
            # Flip image based on self.direction so he faces the movement direction
            self.image = pygame.transform.flip(frame_img, True, False) if self.direction == -1 else frame_img
            self.last_update = now

        if animation_state in [AnimationState.ENTERING, AnimationState.LEAVING]:
            self.state = "walk"
        elif animation_state == AnimationState.TALKING:
            self.state = "Idle"
        self.rect.center = (self.x, self.y)

    def get_image_as_cv2(self):
        data = pygame.image.tostring(self.image, "RGBA")
        img = np.frombuffer(data, dtype=np.uint8).reshape((self.image.get_height(), self.image.get_width(), 4))
        return cv2.cvtColor(img, cv2.COLOR_RGBA2BGRA)

def overlay_image_alpha(background, overlay, pos):
    x, y = pos
    h, w = overlay.shape[:2]
    bg_h, bg_w = background.shape[:2]
    if x < 0 or y < 0 or x + w > bg_w or y + h > bg_h:
        return background
    roi = background[y:y+h, x:x+w]
    alpha = overlay[:, :, 3] / 255.0
    for c in range(3):
        roi[:, :, c] = overlay[:, :, c] * alpha + roi[:, :, c] * (1 - alpha)
    background[y:y+h, x:x+w] = roi
    return background

# ---------- BOT SPEECH & BUBBLE ----------
def speak_line(text):
    # Use edge-tts for a natural and masculine voice.
    def run_tts():
        async def tts_task():
            # "en-US-GuyNeural" is a high-quality masculine voice.
            communicate = edge_tts.Communicate(text, "en-US-GuyNeural")
            await communicate.save("bot_speech.mp3")
        asyncio.run(tts_task())
        # Play the generated audio using pygame.
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        pygame.mixer.music.load("bot_speech.mp3")
        pygame.mixer.music.play()
    threading.Thread(target=run_tts, daemon=True).start()

def draw_speech_bubble(frame, text, pos):
    x, y = pos
    max_chars = 40
    wrapped_text = textwrap.wrap(text, width=max_chars)
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.5
    thickness = 1
    padding = 10
    line_spacing = 5
    max_line_width = 0
    line_height = 0
    for line in wrapped_text:
        (line_width, lh), _ = cv2.getTextSize(line, font, font_scale, thickness)
        max_line_width = max(max_line_width, line_width)
        line_height = lh
    bubble_width = max_line_width + 2 * padding
    bubble_height = len(wrapped_text) * (line_height + line_spacing) + 2 * padding - line_spacing
    top_left = (x, y - bubble_height)
    bottom_right = (x + bubble_width, y)
    cv2.rectangle(frame, top_left, bottom_right, (255, 255, 255), -1)
    cv2.rectangle(frame, top_left, bottom_right, (0, 0, 0), 2)
    for i, line in enumerate(wrapped_text):
        text_x = x + padding
        text_y = y - bubble_height + padding + i * (line_height + line_spacing) + line_height
        cv2.putText(frame, line, (text_x, text_y), font, font_scale, (0, 0, 0), thickness)

# ---------- USER SIDE DETECTION ----------
def detect_user_side(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    left_sum = np.sum(gray[:, :w//2])
    right_sum = np.sum(gray[:, w//2:])
    return -1 if left_sum < right_sum else 1

# ---------- UI HELPER ----------
def draw_rounded_rect(surface, rect, color, corner_radius):
    pygame.draw.rect(surface, color, rect, border_radius=corner_radius)

# ---------- MAIN FUNCTION ----------
def main():
    parsed_script = load_script(SCRIPT_FILE)
    total_lines = len(parsed_script)
    current_index = 0

    # For suggestions (thread-safe)
    suggestion_for_current_line = None
    next_suggestion = None
    suggestion_lock = threading.Lock()

    # Function to set suggestion for next dialogue (if applicable)
    def set_next_suggestion(suggestion):
        nonlocal next_suggestion
        with suggestion_lock:
            next_suggestion = suggestion

    # Pre-fetch suggestion only if next dialogue exists and is from a human.
    if total_lines > 1 and parsed_script[1][0].lower() != "bot":
        fetch_suggestions_async(parsed_script[1][1], set_next_suggestion)
    else:
        next_suggestion = None

    pygame.init()
    pygame.mixer.init()
    transcript_screen = pygame.display.set_mode(
        (INIT_TRANSCRIPT_WIDTH, INIT_TRANSCRIPT_HEIGHT),
        pygame.RESIZABLE
    )
    pygame.display.set_caption("Transcript & Suggestions")

    header_font = pygame.font.SysFont("Arial", 32, bold=True)
    transcript_font = pygame.font.SysFont("Arial", 24)
    suggestion_font = pygame.font.SysFont("Arial", 20)

    clock = pygame.time.Clock()
    transcript_window_width = INIT_TRANSCRIPT_WIDTH
    transcript_window_height = INIT_TRANSCRIPT_HEIGHT

    # "Next" button settings.
    button_width, button_height = 140, 50
    button_corner_radius = 10
    click_cooldown = 0.3
    last_click_time = 0

    cap = cv2.VideoCapture(0)
    cv2.namedWindow("Video Feed", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Video Feed", VIDEO_WIDTH, VIDEO_HEIGHT)
    ret, first_frame = cap.read()
    user_side = detect_user_side(first_frame) if ret else 1

    # Setup ElfKing: character enters from off-screen and exits in the same direction.
    if user_side == 1:
        start_x = -50
        enter_direction, leave_direction = 1, 1
    else:
        start_x = VIDEO_WIDTH + 50
        enter_direction, leave_direction = -1, -1

    elf_king = ElfKing(start_x, VIDEO_HEIGHT - 50, scale_factor=3.0)
    elf_king.direction = enter_direction
    elf_king.base_y = VIDEO_HEIGHT - (elf_king.image.get_height() // 2) - 10
    elf_king.y = elf_king.base_y
    animation_state = AnimationState.ENTERING
    elf_introduced = False
    exit_phase = False
    bot_spoken_for_index = -1

    running = True
    while running:
        # ---------- Event Handling ----------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.VIDEORESIZE:
                transcript_window_width = event.w
                transcript_window_height = event.h
                transcript_screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                current_click_time = time.time()
                if current_click_time - last_click_time < click_cooldown:
                    continue
                last_click_time = current_click_time

                button_x = transcript_window_width - button_width - 30
                button_y = transcript_window_height - button_height - 30
                button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
                if button_rect.collidepoint(event.pos):
                    if current_index < total_lines - 1:
                        current_index += 1
                        print(f"Next dialogue clicked, new index: {current_index}")
                        # If the new current dialogue is from human, set suggestion.
                        if parsed_script[current_index][0].lower() != "bot":
                            with suggestion_lock:
                                suggestion_for_current_line = next_suggestion
                                next_suggestion = None
                        else:
                            suggestion_for_current_line = None
                        # Pre-fetch suggestion for the following dialogue if available and if it's human.
                        if current_index + 1 < total_lines and parsed_script[current_index + 1][0].lower() != "bot":
                            fetch_suggestions_async(parsed_script[current_index + 1][1], set_next_suggestion)
                        else:
                            next_suggestion = None
                        elf_introduced = True
                        exit_phase = False

        # ---------- Video Feed (OpenCV) ----------
        ret, frame = cap.read()
        if ret:
            frame = cv2.resize(frame, (VIDEO_WIDTH, VIDEO_HEIGHT))
            if not elf_introduced and not exit_phase:
                if animation_state == AnimationState.ENTERING:
                    elf_king.x += enter_direction * 5
                    center_target = VIDEO_WIDTH // 4
                    if (enter_direction == 1 and elf_king.x >= center_target) or \
                            (enter_direction == -1 and elf_king.x <= center_target):
                        elf_king.x = center_target
                        animation_state = AnimationState.TALKING
                        elf_introduced = True
                elf_king.update(animation_state)
            elif elf_introduced and current_index < total_lines:
                elf_king.x = VIDEO_WIDTH // 4
                elf_king.update(AnimationState.TALKING)
            elif current_index >= total_lines:
                if not exit_phase:
                    exit_phase = True
                    exit_target = VIDEO_WIDTH + 50 if leave_direction == 1 else -(elf_king.rect.width + 50)
                    elf_king.direction = leave_direction
                if leave_direction == 1:
                    if elf_king.x < exit_target:
                        elf_king.x += 5
                    else:
                        elf_king.x = exit_target
                elif leave_direction == -1:
                    if elf_king.x > exit_target:
                        elf_king.x -= 5
                    else:
                        elf_king.x = exit_target
                elf_king.update(AnimationState.LEAVING)

            elf_img = elf_king.get_image_as_cv2()
            pos = (int(elf_king.rect.x), int(elf_king.rect.y))
            frame = overlay_image_alpha(frame, elf_img, pos)

            # Draw speech bubble only for bot lines.
            if current_index < total_lines:
                speaker, line_text = parsed_script[current_index]
                if speaker.lower() == "bot":
                    bubble_x = max(0, int(elf_king.rect.x) - 50)
                    bubble_y = max(200, int(elf_king.rect.y) - (elf_king.image.get_height() // 2))
                    draw_speech_bubble(frame, line_text, (bubble_x, bubble_y))

            cv2.imshow("Video Feed", frame)
        else:
            cv2.imshow("Video Feed", np.zeros((VIDEO_HEIGHT, VIDEO_WIDTH, 3), dtype=np.uint8))
        cv2.waitKey(1)

        # ---------- Transcript & Suggestions Window (Pygame) ----------
        transcript_screen.fill(BG_COLOR)
        margin_left = 30
        margin_top = 80

        wrap_limit_transcript = max(30, (transcript_window_width - 2 * margin_left) // 8)
        wrap_limit_suggestions = max(20, (transcript_window_width - 2 * margin_left) // 10)

        button_x = transcript_window_width - button_width - 30
        button_y = transcript_window_height - button_height - 30
        button_rect = pygame.Rect(button_x, button_y, button_width, button_height)

        header_text = header_font.render("Transcript", True, HEADER_COLOR)
        transcript_screen.blit(header_text, (margin_left, 20))

        divider_y = transcript_window_height - 250
        transcript_area = pygame.Rect(
            margin_left - 10, margin_top - 10,
            transcript_window_width - 2 * margin_left + 20,
            divider_y - margin_top + 10
        )
        pygame.draw.rect(transcript_screen, BORDER_COLOR, transcript_area, 2)

        y_offset = margin_top
        for i, (speaker, line) in enumerate(parsed_script):
            wrapped_lines = textwrap.wrap(line, width=wrap_limit_transcript)
            prefix = ">>>" if i == current_index else "   "
            line_color = (0, 0, 150) if i == current_index else TEXT_COLOR
            transcript_line = f"{prefix} {speaker}: {wrapped_lines[0] if wrapped_lines else ''}"
            rendered_line = transcript_font.render(transcript_line, True, line_color)
            transcript_screen.blit(rendered_line, (margin_left, y_offset))
            y_offset += rendered_line.get_height() + 5
            for extra_line in wrapped_lines[1:]:
                extra_render = transcript_font.render("    " + extra_line, True, TEXT_COLOR)
                transcript_screen.blit(extra_render, (margin_left, y_offset))
                y_offset += extra_render.get_height() + 5

        pygame.draw.line(transcript_screen, DIVIDER_COLOR, (margin_left, divider_y),
                         (transcript_window_width - margin_left, divider_y), 2)

        # Show suggestion variations if available and current dialogue is human.
        if suggestion_for_current_line and parsed_script[current_index][0].lower() != "bot":
            suggestion_title = suggestion_font.render("Variations:", True, HEADER_COLOR)
            transcript_screen.blit(suggestion_title, (margin_left, divider_y + 10))
            line_height = suggestion_font.get_height() + 2
            sug_y = divider_y + 10 + suggestion_title.get_height() + 5
            suggestion_lines = textwrap.wrap(suggestion_for_current_line, width=wrap_limit_suggestions)
            for sug_line in suggestion_lines:
                if sug_y + line_height > button_y - 10:
                    ellipses_render = suggestion_font.render("...", True, TEXT_COLOR)
                    transcript_screen.blit(ellipses_render, (margin_left, sug_y))
                    break
                sug_render = suggestion_font.render(sug_line, True, TEXT_COLOR)
                transcript_screen.blit(sug_render, (margin_left, sug_y))
                sug_y += line_height

        if button_rect.collidepoint(pygame.mouse.get_pos()):
            draw_rounded_rect(transcript_screen, button_rect, BUTTON_HOVER_COLOR, button_corner_radius)
        else:
            draw_rounded_rect(transcript_screen, button_rect, BUTTON_COLOR, button_corner_radius)
        btn_text = transcript_font.render("Next", True, (255, 255, 255))
        btn_text_rect = btn_text.get_rect(center=button_rect.center)
        transcript_screen.blit(btn_text, btn_text_rect)

        pygame.display.flip()
        clock.tick(FPS)

        # ---------- Trigger Bot Speech Once ----------
        if current_index < total_lines:
            speaker, line_text = parsed_script[current_index]
            if speaker.lower() == "bot" and current_index != bot_spoken_for_index:
                speak_line(line_text)
                bot_spoken_for_index = current_index

    cap.release()
    cv2.destroyAllWindows()
    pygame.quit()

if __name__ == "__main__":
    main()