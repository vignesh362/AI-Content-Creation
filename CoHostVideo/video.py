import cv2
import numpy as np
import pygame
import os
from animation import ElfKing, AnimationState, split_text, generate_tts_audio, FONT, WIDTH, HEIGHT, FPS, TOTAL_FRAMES, TTS_FOLDER

# Initialize webcam capture via OpenCV
cap = cv2.VideoCapture(0)

# Initialize Pygame and mixer (make sure this happens after importing the module)
pygame.init()
pygame.mixer.init(frequency=24000, size=-16, channels=2, buffer=2048)
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Elf King Animation with Webcam Overlay")
clock = pygame.time.Clock()

# Create an instance of ElfKing
elf_king = ElfKing(-100, HEIGHT // 2)

# Use the same dialogue as before (or change as desired)
DIALOGUE_SCRIPT = """Thank you, Jake! I’ll take it from here. Tech lovers, I’m the Tech King, and the wait is finally over! The iPhone 15 Pro Max has arrived—lighter, faster, and smarter than ever. But the real question is, is it truly worth the upgrade?"""
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

    # Capture the webcam frame
    ret, frame = cap.read()
    if ret:
        # Convert frame from BGR to RGB and resize to match screen dimensions
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = cv2.resize(frame, (WIDTH, HEIGHT))
        # Create a Pygame surface from the webcam frame
        webcam_surface = pygame.image.frombuffer(frame.tobytes(), (WIDTH, HEIGHT), "RGB")
        screen.blit(webcam_surface, (0, 0))
    else:
        screen.fill((0, 0, 0))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Animation state machine
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

    # Overlay the ElfKing animation on top of the webcam feed
    elf_king.draw(screen)
    pygame.display.flip()
    frame_counter += 1

cap.release()
pygame.mixer.quit()
pygame.quit()