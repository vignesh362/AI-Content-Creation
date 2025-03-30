import pygame
import os
import math
from gtts import gTTS

# ---------- SETTINGS ----------
WIDTH, HEIGHT = 800, 600
FPS = 60
TOTAL_FRAMES = 1800
SCALE_FACTOR = 2.0

STATES = ["Idle", "walk", "Run", "jump", "fall"]

ANIMATION_PATHS = {
    "Idle":  "extracted_elfking/Idle",
    "walk":  "extracted_elfking/walk",
    "Run":   "extracted_elfking/Run",
    "jump":  "extracted_elfking/jump",
    "fall":  "extracted_elfking/fall"
}

DIALOGUE_SCRIPT = """Thank you, Jake! I’ll take it from here. Tech lovers, I’m the Tech King, and the wait is finally over! The iPhone 15 Pro Max has arrived—lighter, faster, and smarter than ever. But the real question is, is it truly worth the upgrade?"""

TTS_FOLDER = "tts_audio"
FRAMES_FOLDER = "temp_frames"

# Ensure required directories exist
os.makedirs(TTS_FOLDER, exist_ok=True)
os.makedirs(FRAMES_FOLDER, exist_ok=True)

# Initialize Pygame and mixer
pygame.init()
pygame.mixer.init(frequency=24000, size=-16, channels=2, buffer=2048)

FONT = pygame.font.SysFont("Arial", 20)

# ---------- ANIMATION STATE ----------
class AnimationState:
    ENTERING = 0
    TALKING = 1
    WAITING = 2
    LEAVING = 3
    FINISHED = 4

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
                (int(image.get_width() * scale_factor), int(image.get_height() * scale_factor))
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
    def __init__(self, x, y):
        super().__init__()
        self.x = x
        self.y = y
        self.base_y = y  # Store the initial y position
        self.state = "walk"
        self.frame_index = 0
        self.animations = {state: load_frames_from_folder(ANIMATION_PATHS[state], SCALE_FACTOR)
                           for state in STATES}
        # Use the first frame from the initial state; add fallback if missing.
        self.image = self.animations[self.state][0] if self.animations[self.state] else None
        if self.image:
            self.rect = self.image.get_rect(center=(x, y))
        else:
            self.rect = pygame.Rect(x, y, 50, 50)
        self.last_update = pygame.time.get_ticks()
        self.speech_text = ""
        self.direction = 1
        self.idle_offset = 0

    def update(self, animation_state):
        now = pygame.time.get_ticks()

        # Update animation frame if available
        if self.animations[self.state]:
            if now - self.last_update > 100:
                self.frame_index = (self.frame_index + 1) % len(self.animations[self.state])
                self.image = self.animations[self.state][self.frame_index]
                if self.direction == -1:
                    self.image = pygame.transform.flip(self.image, True, False)
                self.last_update = now

        # State-specific behavior
        if animation_state == AnimationState.ENTERING:
            self.state = "walk"
            self.x += 2
            if self.x >= WIDTH // 2:
                self.state = "Idle"
                return True
        elif animation_state == AnimationState.TALKING:
            self.state = "Idle"
            self.idle_offset = math.sin(now / 500) * 3
            self.y = self.base_y + self.idle_offset
        elif animation_state == AnimationState.LEAVING:
            self.state = "walk"
            self.direction = 1
            self.x += 2
            if self.x > WIDTH + 100:
                return True

        self.rect.center = (self.x, self.y)
        return False

    def draw(self, surface):
        if self.image:
            surface.blit(self.image, self.rect)
        if self.speech_text:
            draw_speech_bubble(surface, self.speech_text, (self.rect.centerx, self.rect.top - 20), FONT)

# ---------- MAIN ANIMATION (Standalone) ----------
if __name__ == "__main__":
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Elf King Animation")
    clock = pygame.time.Clock()

    elf_king = ElfKing(-100, HEIGHT // 2)
    dialogue_chunks = split_text(DIALOGUE_SCRIPT)
    tts_files = generate_tts_audio(dialogue_chunks, TTS_FOLDER)
    current_chunk = 0
    audio_playing = False
    current_sound = None

    audio_chunks = []
    for file in tts_files:
        try:
            sound = pygame.mixer.Sound(file)
            audio_chunks.append(sound)
        except Exception as e:
            print(f"Error loading audio file: {e}")

    animation_state = AnimationState.ENTERING
    running = True
    frame_counter = 0

    while running and frame_counter < TOTAL_FRAMES:
        clock.tick(FPS)
        current_time = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Update state machine
        if animation_state == AnimationState.ENTERING:
            if elf_king.update(animation_state):
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
        elif animation_state == AnimationState.LEAVING:
            if elf_king.update(animation_state):
                animation_state = AnimationState.FINISHED
                running = False

        screen.fill((255, 255, 255))
        elf_king.draw(screen)
        pygame.display.flip()
        frame_counter += 1

    pygame.mixer.quit()
    pygame.quit()