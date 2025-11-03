import pygame as pg
import random
import sys
from collections import Counter

pg.init()
pg.font.init()

Winght, Hight = 800, 600
screen = pg.display.set_mode((Winght,Hight), pg.RESIZABLE)
pg.display.set_caption("Wordle by Biohazard group")
icon = pg.image.load("icon.png")
pg.display.set_icon(icon)
Colors = {
    "WHITE": (255, 255, 255), "BLACK": (0, 0, 0),
    "GREEN": (106, 170, 100), "YELLOW": (201, 180, 88),
    "GRAY": (120, 124, 126),
    "LIGHT_GRAY": (211, 211, 211),
    "KEY_DEFAULT": (129, 131, 132),
    "KEY_USED": (58, 58, 60),
    "RED": (200, 70, 70)
}

Fonts =  {}
def UpdateFnonts(wight, hight):
    base_size = min(wight, hight)
    font_name = 'Arial'
    try:
        Fonts["letter"] = pg.font.SysFont(font_name, int(base_size * 0.055), bold=True)
        Fonts["menu"] = pg.font.SysFont(font_name, int(base_size * 0.05), bold=True)
        Fonts["stats"] = pg.font.SysFont(font_name, int(base_size * 0.036))
        Fonts["message"] = pg.font.SysFont(font_name, int(base_size * 0.03))
        Fonts["key"] = pg.font.SysFont(font_name, int(base_size * 0.023), bold=True)
        Fonts["end_game"] = pg.font.SysFont(font_name, int(base_size * 0.06), bold=True)
    except Exception:
        Fonts["letter"] = pg.font.Font(None, int(base_size * 0.07))
        Fonts["menu"] = pg.font.Font(None, int(base_size * 0.06))
        Fonts["stats"] = pg.font.Font(None, int(base_size * 0.04))
        Fonts["message"] = pg.font.Font(None, int(base_size * 0.035))
        Fonts["key"] = pg.font.Font(None, int(base_size * 0.03))
        Fonts["end_game"] = pg.font.Font(None, int(base_size * 0.07))
UpdateFnonts(Winght, Hight)

def main_menu():
    global Winght, Hight, screen
    running = True
    while running:
        screen.fill(Colors["LIGHT_GRAY"])
        title_text = Fonts["menu"].render("Statistics", True, Colors["BLACK"])
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            elif event.type == pg.VIDEORESIZE:
                Winght, Hight = event.w, event.h
                screen = pg.display.set_mode((Winght, Hight), pg.RESIZABLE)
        
def display_state(state):
    pass

    
if __name__ == "__main__":
    main_menu()