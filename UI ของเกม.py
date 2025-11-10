import pygame
import sys
import os

pygame.init()

#  หน้าจอแบบปรับขนาดได้
SCREEN_W, SCREEN_H = 500, 650
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.RESIZABLE)
pygame.display.set_caption("เกมทายคำภาษาอังกฤษ")

CLOCK = pygame.time.Clock()
FPS = 60

#  สีหลัก
BG_COLOR = (35, 65, 150)
BUTTON_COLOR = (80, 150, 255)
BUTTON_HOVER = (130, 180, 255)
TEXT_COLOR = (255, 255, 255)
GRAY = (200, 200, 200)

#  ฟอนต์
def get_font(size):
    for f in ["Poppins-Regular.ttf", "Montserrat-Regular.ttf", "Kanit-Regular.ttf"]:
        if os.path.exists(f):
            return pygame.font.Font(f, size)
    return pygame.font.SysFont("segoeui", size, bold=True)

#  สร้างปุ่ม
def create_buttons(w, h, mode="menu"):
    btn_width = max(180, min(300, int(w * 0.4)))
    btn_height = max(45, min(70, int(h * 0.07)))
    gap = btn_height + 20
    total_height = 3 * btn_height + 2 * 20
    start_y = max(120, h // 2 - total_height // 2)
    center_x = w // 2 - btn_width // 2

    if mode == "menu":
        return {
            "Play": pygame.Rect(center_x, start_y, btn_width, btn_height),
            "Option": pygame.Rect(center_x, start_y + gap, btn_width, btn_height),
            "Exit": pygame.Rect(center_x, start_y + gap * 2, btn_width, btn_height)
        }
    elif mode == "mode":
        return {
            "Classic": pygame.Rect(center_x, start_y, btn_width, btn_height),
            "Unlimited": pygame.Rect(center_x, start_y + gap, btn_width, btn_height),
            "Hard": pygame.Rect(center_x, start_y + gap * 2, btn_width, btn_height),
            "Back": pygame.Rect(center_x, start_y + gap * 3, btn_width, btn_height)
        }
    elif mode == "game":
        return {
            "Back": pygame.Rect(30, h - 60, 110, 45)
        }

#  วาดปุ่ม
def draw_button(screen, rect, text, mx, my, font):
    is_hover = rect.collidepoint((mx, my))
    color = BUTTON_HOVER if is_hover else BUTTON_COLOR
    pygame.draw.rect(screen, color, rect, border_radius=20)
    pygame.draw.rect(screen, TEXT_COLOR, rect, 3, border_radius=20)
    label = font.render(text, True, TEXT_COLOR)
    label_rect = label.get_rect(center=rect.center)
    screen.blit(label, label_rect)

#  วาดชื่อเกม
def draw_title(screen, w, text, y=100):
    font_size = max(28, min(64, w // 14))
    title_font = get_font(font_size)
    label = title_font.render(text, True, TEXT_COLOR)
    label_rect = label.get_rect(center=(w // 2, y))
    screen.blit(label, label_rect)

#  วาดช่องคำ (กริด)
def draw_word_grid(screen, w, h):
    cols, rows = 5, 6
    grid_area_h = h * 0.4  # ความสูงของโซนกริดทั้งหมด
    box_size = min(w // (cols + 2), int(grid_area_h // rows))
    start_x = w // 2 - (cols * box_size) // 2
    start_y = 130

    for r in range(rows):
        for c in range(cols):
            rect = pygame.Rect(start_x + c * box_size, start_y + r * box_size, box_size - 5, box_size - 5)
            pygame.draw.rect(screen, TEXT_COLOR, rect, 3, border_radius=5)

#  วาดแป้นพิมพ์
def draw_keyboard(screen, w, h):
    font_kb = get_font(24)
    key_w, key_h = max(30, w // 20), max(35, h // 20)
    rows = ["QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"]

    start_y = h - 250  # ยกขึ้นจากขอบล่างให้ไม่ชน
    for i, row in enumerate(rows):
        start_x = w // 2 - len(row) * (key_w + 5) // 2
        for j, ch in enumerate(row):
            rect = pygame.Rect(start_x + j * (key_w + 5), start_y + i * (key_h + 5), key_w, key_h)
            pygame.draw.rect(screen, BUTTON_COLOR, rect, border_radius=8)
            pygame.draw.rect(screen, TEXT_COLOR, rect, 2, border_radius=8)
            label = font_kb.render(ch, True, TEXT_COLOR)
            label_rect = label.get_rect(center=rect.center)
            screen.blit(label, label_rect)

#  เริ่มเกม
current_screen = "menu"
running = True

while running:
    mx, my = pygame.mouse.get_pos()
    SCREEN_W, SCREEN_H = screen.get_size()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.VIDEORESIZE:
            SCREEN_W, SCREEN_H = event.w, event.h
            screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.RESIZABLE)
        if event.type == pygame.MOUSEBUTTONDOWN:
            if current_screen == "menu":
                buttons = create_buttons(SCREEN_W, SCREEN_H, "menu")
                if buttons["Play"].collidepoint((mx, my)):
                    current_screen = "mode"
                elif buttons["Exit"].collidepoint((mx, my)):
                    running = False
            elif current_screen == "mode":
                buttons = create_buttons(SCREEN_W, SCREEN_H, "mode")
                if buttons["Back"].collidepoint((mx, my)):
                    current_screen = "menu"
                elif any(buttons[m].collidepoint((mx, my)) for m in ["Classic", "Unlimited", "Hard"]):
                    current_screen = "game"
            elif current_screen == "game":
                buttons = create_buttons(SCREEN_W, SCREEN_H, "game")
                if buttons["Back"].collidepoint((mx, my)):
                    current_screen = "mode"

    #  พื้นหลังเรียบ
    screen.fill(BG_COLOR)

    # ฟอนต์หลัก
    font = get_font(max(22, min(42, SCREEN_W // 20)))

    #สลับหน้า
    if current_screen == "menu":
        draw_title(screen, SCREEN_W, "WORD GUESS GAME")
        buttons = create_buttons(SCREEN_W, SCREEN_H, "menu")
        for text, rect in buttons.items():
            draw_button(screen, rect, text, mx, my, font)

    elif current_screen == "mode":
        draw_title(screen, SCREEN_W, "MODE")
        buttons = create_buttons(SCREEN_W, SCREEN_H, "mode")
        for text, rect in buttons.items():
            draw_button(screen, rect, text, mx, my, font)

    elif current_screen == "game":
        draw_title(screen, SCREEN_W, "CLASSIC MODE", 60)
        draw_word_grid(screen, SCREEN_W, SCREEN_H)
        draw_keyboard(screen, SCREEN_W, SCREEN_H)
        buttons = create_buttons(SCREEN_W, SCREEN_H, "game")
        for text, rect in buttons.items():
            draw_button(screen, rect, text, mx, my, font)

    pygame.display.update()
    CLOCK.tick(FPS)

pygame.quit()
sys.exit()
