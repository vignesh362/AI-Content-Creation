import cv2
import numpy as np
import pygame
import os
import math
from gtts import gTTS

# ---------- SETTINGS ----------
WIDTH, HEIGHT = 800, 600
FPS = 60
SCALE_FACTOR = 4.0
TTS_FOLDER = "tts_audio"

os.makedirs(TTS_FOLDER, exist_ok=True)

# ---------- ANIMATION STATE ----------
class AnimationState:
    ENTERING = 0
    TALKING = 1
    LEAVING = 2
    FINISHED = 3

# ---------- HELPER FUNCTIONS ----------
def split_text(text, max_length=50):
    words = text.split()
    chunks = []
    current_chunk = []
    for word in words:
        if len(' '.join(current_chunk + [word])) <= max_length:
            current_chunk.append(word)
        else:
            chunks.append(' '.join(current_chunk))
            current_chunk = [word]
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    return chunks

def generate_tts_audio(text_chunks, folder):
    audio_files = []
    for i, chunk in enumerate(text_chunks):
        filename = os.path.join(folder, f'chunk_{i}.mp3')
        if not os.path.exists(filename):
            tts = gTTS(text=chunk, lang='en')
            tts.save(filename)
        audio_files.append(filename)
    return audio_files

def load_frames_from_folder(folder_path, scale_factor):
    frames = []
    if not os.path.exists(folder_path):
        print(f"Folder not found: {folder_path}")
        return frames
    for file in sorted(os.listdir(folder_path)):
        if file.endswith('.png'):
            image = pygame.image.load(os.path.join(folder_path, file)).convert_alpha()
            scaled_image = pygame.transform.scale(
                image,
                (int(image.get_width() * scale_factor),
                 int(image.get_height() * scale_factor))
            )
            frames.append(scaled_image)
    return frames

def draw_speech_bubble(surface, text, pos, font):
    padding = 10
    text_surf = font.render(text, True, (0, 0, 0))
    text_rect = text_surf.get_rect()
    bubble_rect = pygame.Rect(
        pos[0] - text_rect.width // 2 - padding,
        pos[1] - text_rect.height - padding,
        text_rect.width + padding * 2,
        text_rect.height + padding * 2
    )
    pygame.draw.rect(surface, (255, 255, 255), bubble_rect, border_radius=10)
    pygame.draw.rect(surface, (0, 0, 0), bubble_rect, 2, border_radius=10)
    surface.blit(text_surf, (bubble_rect.x + padding, bubble_rect.y + padding))

# ---------- ELF KING SPRITE ----------
class ElfKing(pygame.sprite.Sprite):
    def __init__(self, x, y, scale_factor=2.0):
        super().__init__()
        self.x = x
        self.y = y
        self.base_y = y  # For keeping on the base
        self.state = "walk"  # starting with walk animation
        self.frame_index = 0

        # Load minimal animations from folders (adjust to your actual paths)
        self.animations = {
            "Idle": load_frames_from_folder("extracted_elfking/Idle", scale_factor),
            "walk": load_frames_from_folder("extracted_elfking/walk", scale_factor)
        }
        # Use a default image if animation frames are missing.
        if self.animations[self.state]:
            self.image = self.animations[self.state][0]
        else:
            self.image = pygame.Surface((50, 50))
            self.image.fill((0, 255, 0))

        self.rect = self.image.get_rect(center=(x, y))
        self.last_update = pygame.time.get_ticks()
        self.speech_text = ""
        self.direction = 1  # 1 for right, -1 for left
        self.idle_offset = 0

    def update(self, animation_state):
        now = pygame.time.get_ticks()
        if self.animations[self.state]:
            if now - self.last_update > 100:
                self.frame_index = (self.frame_index + 1) % len(self.animations[self.state])
                frame_img = self.animations[self.state][self.frame_index]
                # Flip if moving left
                if self.direction == -1:
                    frame_img = pygame.transform.flip(frame_img, True, False)
                self.image = frame_img
                self.last_update = now

        if animation_state == AnimationState.ENTERING:
            self.state = "walk"
        elif animation_state == AnimationState.TALKING:
            self.state = "Idle"
            # Keep y fixed at the base:
            self.y = self.base_y
        elif animation_state == AnimationState.LEAVING:
            self.state = "walk"

        self.rect.center = (self.x, self.y)

    def draw(self, surface):
        surface.blit(self.image, self.rect)
        if self.speech_text:
            font = pygame.font.SysFont("Arial", 20)
            draw_speech_bubble(surface, self.speech_text, (self.rect.centerx, self.rect.top - 20), font)

# ---------- VERY NAIVE DETECTION OF USER SIDE ----------
def detect_user_side(frame):
    """
    Returns:
      -1 if user is mostly on the left half,
      +1 if user is mostly on the right half,
       0 if uncertain.
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    left_half = gray[:, :w//2]
    right_half = gray[:, w//2:]

    sum_left = np.sum(left_half)
    sum_right = np.sum(right_half)

    if sum_left < sum_right:
        return -1  # user on left
    else:
        return 1   # user on right

# ---------- MAIN PROGRAM ----------
def main():
    pygame.init()
    pygame.mixer.init(frequency=24000, size=-16, channels=2, buffer=2048)
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Elf King - Walk on the Base")
    clock = pygame.time.Clock()

    # 1. Grab one frame from the webcam to decide user side
    cap = cv2.VideoCapture(0)
    ret, first_frame = cap.read()
    user_side = 1  # default
    if ret:
        user_side = detect_user_side(first_frame)
    else:
        print("Could not capture initial frame for user side detection.")

    # 2. Decide from which side the ElfKing enters
    if user_side == -1:
        start_x = WIDTH + 100  # Enter from right if user is on left
        enter_direction = -1
        leave_direction = 1
    else:
        start_x = -100  # Enter from left if user is on right
        enter_direction = 1
        leave_direction = -1

    # 3. Create the ElfKing and set its y to the base (bottom of the frame)
    # We set y so the bottom of the sprite touches the bottom of the screen.
    elf_king = ElfKing(start_x, HEIGHT - 20, SCALE_FACTOR)  # 20 pixels offset for a floor margin
    elf_king.direction = enter_direction
    # Adjust base_y to keep the character at the bottom.
    elf_king.base_y = HEIGHT - (elf_king.image.get_height() // 2) - 10  # extra margin if needed
    elf_king.y = elf_king.base_y

    # 4. Setup dialogue
    DIALOGUE_SCRIPT = (
        "Thank you, Jake! I’ll take it from here. Tech lovers, I’m the Tech King, "
        "and the wait is finally over! The iPhone 15 Pro Max has arrived—lighter, faster, "
        "and smarter than ever. But the real question is, is it truly worth the upgrade?"
    )
    dialogue_chunks = split_text(DIALOGUE_SCRIPT)
    tts_files = generate_tts_audio(dialogue_chunks, TTS_FOLDER)
    audio_chunks = []
    for file in tts_files:
        try:
            sound = pygame.mixer.Sound(file)
            audio_chunks.append(sound)
        except Exception as e:
            print(f"Error loading audio file: {e}")
    current_chunk = 0
    audio_playing = False
    current_sound = None

    animation_state = AnimationState.ENTERING
    running = True

    while running:
        clock.tick(FPS)
        ret, frame = cap.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, (WIDTH, HEIGHT))
            webcam_surface = pygame.image.frombuffer(frame.tobytes(), (WIDTH, HEIGHT), "RGB")
            screen.blit(webcam_surface, (0, 0))
        else:
            screen.fill((0, 0, 0))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        if animation_state == AnimationState.ENTERING:
            elf_king.update(animation_state)
            # Only update x to move horizontally
            elf_king.x += enter_direction
            # Check if near center horizontally
            center_target = (WIDTH // 2) - (elf_king.image.get_width() // 2) * enter_direction
            if (enter_direction == 1 and elf_king.x >= center_target) or \
                    (enter_direction == -1 and elf_king.x <= center_target):
                elf_king.x = center_target
                animation_state = AnimationState.TALKING

        elif animation_state == AnimationState.TALKING:
            elf_king.update(animation_state)
            if current_chunk < len(dialogue_chunks):
                elf_king.speech_text = dialogue_chunks[current_chunk]
                if not audio_playing and current_chunk < len(audio_chunks):
                    current_sound = audio_chunks[current_chunk]
                    current_sound.play()
                    audio_playing = True
                if audio_playing and not pygame.mixer.get_busy():
                    audio_playing = False
                    current_chunk += 1
            else:
                animation_state = AnimationState.LEAVING
                elf_king.speech_text = ""
                elf_king.direction = leave_direction

        elif animation_state == AnimationState.LEAVING:
            elf_king.update(animation_state)
            elf_king.x += leave_direction
            if leave_direction == 1 and elf_king.x > WIDTH + elf_king.image.get_width():
                animation_state = AnimationState.FINISHED
                running = False
            elif leave_direction == -1 and elf_king.x < -elf_king.image.get_width():
                animation_state = AnimationState.FINISHED
                running = False

        elf_king.draw(screen)
        pygame.display.flip()

    cap.release()
    pygame.mixer.quit()
    pygame.quit()

if __name__ == "__main__":
    main()