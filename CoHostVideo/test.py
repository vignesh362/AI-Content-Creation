import pygame
import sys
import os

pygame.init()

# ---------------------- SCREEN SETUP ----------------------
SCREEN_WIDTH, SCREEN_HEIGHT = 1000, 800
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Two Characters, Sequential Animations")

# Colors
WHITE = (255, 255, 255)

# ---------------------- FRAME DIMENSIONS ----------------------
# These represent the original frame dimensions in your sprite sheets.
SPRITE_WIDTH = 128
SPRITE_HEIGHT = 128

# ---------------------- SCALING FACTORS ----------------------
# Adjust these scaling factors as desired for each character.
c2_scale = 2.0   # Character2 scaling factor
c3_scale = 2.0   # Character3 scaling factor
elf_scale = 2.0  # Elf King scaling factor

# Animation speed
FPS = 12  # frames per second

clock = pygame.time.Clock()

# ---------------------- LOADING SPRITE SHEETS ----------------------
# character2 images
c2_attack_sheet      = pygame.image.load("character2/Attack.png").convert_alpha()
c2_book_sheet        = pygame.image.load("character2/Book.png").convert_alpha()
c2_dialogue_sheet    = pygame.image.load("character2/Dialogue.png").convert_alpha()
c2_idle_sheet        = pygame.image.load("character2/Idle.png").convert_alpha()
c2_protection_sheet  = pygame.image.load("character2/Protection.png").convert_alpha()
c2_walk_sheet        = pygame.image.load("character2/Walk.png").convert_alpha()

# character3 images
c3_attack_sheet = pygame.image.load("character3/Attack.png").convert_alpha()
c3_dead_sheet   = pygame.image.load("character3/Dead.png").convert_alpha()
c3_hurt_sheet   = pygame.image.load("character3/Hurt.png").convert_alpha()
c3_idle_sheet   = pygame.image.load("character3/Idle.png").convert_alpha()
c3_run_sheet    = pygame.image.load("character3/Run.png").convert_alpha()
c3_walk_sheet   = pygame.image.load("character3/Walk.png").convert_alpha()

# ---------------------- HELPER FUNCTION: LOAD FRAMES ----------------------
def load_frames(sheet, scale=1):
    """
    Extract frames from a sprite sheet using fixed frame dimensions (SPRITE_WIDTH, SPRITE_HEIGHT).
    Scales each frame by the given scale factor.
    Assumes frames are laid out in a grid (rows x cols).
    """
    sheet_width, sheet_height = sheet.get_size()
    frames = []
    cols = sheet_width // SPRITE_WIDTH
    rows = sheet_height // SPRITE_HEIGHT
    for row in range(rows):
        for col in range(cols):
            x = col * SPRITE_WIDTH
            y = row * SPRITE_HEIGHT
            if x + SPRITE_WIDTH <= sheet_width and y + SPRITE_HEIGHT <= sheet_height:
                frame_surface = sheet.subsurface((x, y, SPRITE_WIDTH, SPRITE_HEIGHT))
                if scale != 1:
                    new_w = int(SPRITE_WIDTH * scale)
                    new_h = int(SPRITE_HEIGHT * scale)
                    frame_surface = pygame.transform.scale(frame_surface, (new_w, new_h))
                frames.append(frame_surface)
    return frames

# ---------------------- LOAD ALL ANIMATIONS ----------------------
# Character2 animations (in a sequence):
c2_attack_frames     = load_frames(c2_attack_sheet, scale=c2_scale)
c2_book_frames       = load_frames(c2_book_sheet, scale=c2_scale)
c2_dialogue_frames   = load_frames(c2_dialogue_sheet, scale=c2_scale)
c2_idle_frames       = load_frames(c2_idle_sheet, scale=c2_scale)
c2_protection_frames = load_frames(c2_protection_sheet, scale=c2_scale)
c2_walk_frames       = load_frames(c2_walk_sheet, scale=c2_scale)

c2_animations = [
    ("Attack", c2_attack_frames),
    ("Book", c2_book_frames),
    ("Dialogue", c2_dialogue_frames),
    ("Idle", c2_idle_frames),
    ("Protection", c2_protection_frames),
    ("Walk", c2_walk_frames),
]

# Character3 animations (in a sequence):
c3_attack_frames = load_frames(c3_attack_sheet, scale=c3_scale)
c3_dead_frames   = load_frames(c3_dead_sheet, scale=c3_scale)
c3_hurt_frames   = load_frames(c3_hurt_sheet, scale=c3_scale)
c3_idle_frames   = load_frames(c3_idle_sheet, scale=c3_scale)
c3_run_frames    = load_frames(c3_run_sheet, scale=c3_scale)
c3_walk_frames   = load_frames(c3_walk_sheet, scale=c3_scale)

c3_animations = [
    ("Attack", c3_attack_frames),
    ("Dead",   c3_dead_frames),
    ("Hurt",   c3_hurt_frames),
    ("Idle",   c3_idle_frames),
    ("Run",    c3_run_frames),
    ("Walk",   c3_walk_frames),
]

# ---------------------- 3) ELF KING ANIMATIONS ----------------------
# For the Elf King, load frames from folders.
def load_frames_from_folder(folder_path, scale=1):
    """
    Loads all .png files from 'folder_path' in alphabetical order.
    Returns a list of frames (Pygame surfaces) scaled by the given factor.
    """
    frames = []
    for filename in sorted(os.listdir(folder_path)):
        if filename.lower().endswith(".png"):
            full_path = os.path.join(folder_path, filename)
            image = pygame.image.load(full_path).convert_alpha()
            if scale != 1:
                w = int(image.get_width() * scale)
                h = int(image.get_height() * scale)
                image = pygame.transform.scale(image, (w, h))
            frames.append(image)
    return frames

elf_fall_frames  = load_frames_from_folder("extracted_elfking/fall",  scale=elf_scale)
elf_idle_frames  = load_frames_from_folder("extracted_elfking/Idle",  scale=elf_scale)
elf_jump_frames  = load_frames_from_folder("extracted_elfking/jump",  scale=elf_scale)
elf_run_frames   = load_frames_from_folder("extracted_elfking/Run",   scale=elf_scale)
elf_spell_frames = load_frames_from_folder("extracted_elfking/Spell", scale=elf_scale)
elf_walk_frames  = load_frames_from_folder("extracted_elfking/walk",  scale=elf_scale)

elf_animations = [
    ("fall",  elf_fall_frames),
    ("Idle",  elf_idle_frames),
    ("jump",  elf_jump_frames),
    ("Run",   elf_run_frames),
    ("Spell", elf_spell_frames),
    ("walk",  elf_walk_frames),
]

elf_current_anim_index = 0
elf_current_name, elf_current_frames = elf_animations[elf_current_anim_index]
elf_frame_index = 0

# ---------------------- SETUP ANIMATION STATES ----------------------
# Character2
c2_current_anim_index = 0
c2_current_name, c2_current_frames = c2_animations[c2_current_anim_index]
c2_frame_index = 0

# Character3
c3_current_anim_index = 0
c3_current_name, c3_current_frames = c3_animations[c3_current_anim_index]
c3_frame_index = 0

# ---------------------- MAIN LOOP ----------------------
running = True
while running:
    clock.tick(FPS)
    screen.fill(WHITE)

    # ---------- EVENT HANDLING ----------
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # ---------- UPDATE CHARACTER 2 ----------
    c2_frame_index += 1
    if c2_frame_index >= len(c2_current_frames):
        c2_frame_index = 0
        c2_current_anim_index += 1
        if c2_current_anim_index >= len(c2_animations):
            c2_current_anim_index = 0
        c2_current_name, c2_current_frames = c2_animations[c2_current_anim_index]
        print(f"[Character2] Now playing: {c2_current_name}")

    # ---------- UPDATE CHARACTER 3 ----------
    c3_frame_index += 1
    if c3_frame_index >= len(c3_current_frames):
        c3_frame_index = 0
        c3_current_anim_index += 1
        if c3_current_anim_index >= len(c3_animations):
            c3_current_anim_index = 0
        c3_current_name, c3_current_frames = c3_animations[c3_current_anim_index]
        print(f"[Character3] Now playing: {c3_current_name}")

    # ---------- UPDATE ELF KING ----------
    if elf_current_frames:
        elf_frame_index += 1
        if elf_frame_index >= len(elf_current_frames):
            elf_frame_index = 0
            elf_current_anim_index += 1
            if elf_current_anim_index >= len(elf_animations):
                elf_current_anim_index = 0
            elf_current_name, elf_current_frames = elf_animations[elf_current_anim_index]
            print(f"[ElfKing] Now playing: {elf_current_name}")

    # ---------- DRAW ALL THREE ----------
    # Character2 (top row)
    if c2_current_frames:
        c2_current_frame = c2_current_frames[c2_frame_index]
        # Use the current frame's width and height (scaled)
        c2_x = (SCREEN_WIDTH - c2_current_frame.get_width()) // 2
        c2_y = (SCREEN_HEIGHT // 4) - (c2_current_frame.get_height() // 2)
        screen.blit(c2_current_frame, (c2_x, c2_y))
        font = pygame.font.SysFont(None, 30)
        text_surf_c2 = font.render(f"Character2: {c2_current_name}", True, (0,0,0))
        screen.blit(text_surf_c2, (20, 20))

    # Character3 (middle row)
    if c3_current_frames:
        c3_current_frame = c3_current_frames[c3_frame_index]
        c3_x = (SCREEN_WIDTH - c3_current_frame.get_width()) // 2
        c3_y = (SCREEN_HEIGHT // 2) - (c3_current_frame.get_height() // 2)
        screen.blit(c3_current_frame, (c3_x, c3_y))
        font = pygame.font.SysFont(None, 30)
        text_surf_c3 = font.render(f"Character3: {c3_current_name}", True, (0,0,0))
        screen.blit(text_surf_c3, (20, 60))

    # Elf King (bottom row)
    if elf_current_frames:
        elf_frame_surf = elf_current_frames[elf_frame_index]
        elf_x = (SCREEN_WIDTH - elf_frame_surf.get_width()) // 2
        elf_y = (3 * SCREEN_HEIGHT // 4) - (elf_frame_surf.get_height() // 2)
        screen.blit(elf_frame_surf, (elf_x, elf_y))
        font_elf = pygame.font.SysFont(None, 28)
        text_elf = font_elf.render(f"ElfKing: {elf_current_name}", True, (0,0,0))
        screen.blit(text_elf, (20, 100))

    pygame.display.flip()

pygame.quit()
sys.exit()