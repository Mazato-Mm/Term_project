import pygame
import sys

# ---------------- SETUP ----------------
pygame.init()
pygame.display.set_caption("Wordle - Main Menu")
WIDTH, HEIGHT = 600, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))

# Colors
BG_COLOR = (18, 18, 19)
WHITE = (255, 255, 255)
GREEN = (83, 141, 78)
YELLOW = (181, 159, 59)
GRAY = (120, 124, 126)

# Fonts
TITLE_FONT = pygame.font.SysFont("arialblack", 80)
BUTTON_FONT = pygame.font.SysFont("arialblack", 36)
SUB_FONT = pygame.font.SysFont("arial", 24)

# Button setup
play_button = pygame.Rect(WIDTH/2 - 100, 450, 200, 70)
quit_button = pygame.Rect(WIDTH/2 - 100, 550, 200, 70)

# ---------------- DRAW FUNCTION ----------------
def draw_menu():
    screen.fill(BG_COLOR)

    # Title
    title_text = TITLE_FONT.render("WORDLE", True, WHITE)
    screen.blit(title_text, (WIDTH/2 - title_text.get_width()/2, 200))

    # Subtitle
    sub_text = SUB_FONT.render("Guess the hidden 5-letter word!", True, GRAY)
    screen.blit(sub_text, (WIDTH/2 - sub_text.get_width()/2, 300))

    # Buttons
    pygame.draw.rect(screen, GREEN, play_button, border_radius=10)
    pygame.draw.rect(screen, GRAY, quit_button, border_radius=10)

    play_text = BUTTON_FONT.render("PLAY", True, WHITE)
    quit_text = BUTTON_FONT.render("QUIT", True, WHITE)

    screen.blit(play_text, (play_button.centerx - play_text.get_width()/2,
                            play_button.centery - play_text.get_height()/2))
    screen.blit(quit_text, (quit_button.centerx - quit_text.get_width()/2,
                            quit_button.centery - quit_text.get_height()/2))

    pygame.display.flip()

# ---------------- MAIN LOOP ----------------
running = True
while running:
    draw_menu()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.MOUSEBUTTONDOWN:
            if play_button.collidepoint(event.pos):
                print("✅ Start game (You can link game screen here later)")
                # TODO: switch to main game screen
            elif quit_button.collidepoint(event.pos):
                pygame.quit()
                sys.exit()
