import pygame
import random
import json
import os
import sys
from collections import Counter

pygame.init()
pygame.font.init()
pygame.mixer.init() 

SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "settings.json")
DEFAULT_SETTINGS = {"sound_enabled": True, "bg_volume": 0.3, "fx_volume": 0.5}

WIDTH, HEIGHT = 600, 750
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Wordle BioHazard")
icon = pygame.image.load("icon.png")
SETTING_IMG = pygame.image.load("setting_image.jpg").convert_alpha()
pygame.display.set_icon(icon)

# Colors
COLORS = {
    "WHITE": (255, 255, 255), "BLACK": (0, 0, 0),
    "GREEN": (106, 170, 100), "YELLOW": (201, 180, 88),
    "GRAY": (120, 124, 126),
    "LIGHT_GRAY": (211, 211, 211),
    "KEY_DEFAULT": (129, 131, 132),
    "KEY_USED": (58, 58, 60),
    "RED": (200, 70, 70)
}

def load_settings(path=SETTINGS_FILE):
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # ensure keys exist
                return {
                    "sound_enabled": bool(data.get("sound_enabled", True)),
                    "bg_volume": float(data.get("bg_volume", DEFAULT_SETTINGS["bg_volume"])),
                    "fx_volume": float(data.get("fx_volume", DEFAULT_SETTINGS["fx_volume"]))
                }
    except Exception as e:
        print(f"Could not load settings: {e}")
    # write defaults if missing/corrupt
    save_settings(DEFAULT_SETTINGS, path)
    return DEFAULT_SETTINGS.copy()
def save_settings(settings, path=SETTINGS_FILE):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Could not save settings: {e}")
# ...existing code...

# --- Dynamic Font System ---
FONTS = {}
def update_fonts(width, height):
    base_size = min(width, height)
    font_name = "Arial"
    try:
        FONTS["letter"] = pygame.font.SysFont(font_name, int(base_size * 0.055), bold=True)
        FONTS["menu"] = pygame.font.SysFont(font_name, int(base_size * 0.05), bold=True)
        FONTS["stats"] = pygame.font.SysFont(font_name, int(base_size * 0.036))
        FONTS["message"] = pygame.font.SysFont(font_name, int(base_size * 0.03))
        FONTS["key"] = pygame.font.SysFont(font_name, int(base_size * 0.023), bold=True)
        FONTS["end_game"] = pygame.font.SysFont(font_name, int(base_size * 0.06), bold=True)
    except Exception:
        for key, size in {"letter": 0.07, "menu": 0.06, "stats": 0.04, "message": 0.035, "key": 0.03, "end_game": 0.07}.items():
            FONTS[key] = pygame.font.Font(None, int(base_size * size))

update_fonts(WIDTH, HEIGHT)

# --------------------------------------------------------------------
#  MAIN GAME CLASS
# --------------------------------------------------------------------
class WordleGamePygame:
    def __init__(self, stats_file='wordle_stats_en.json'):
        self.WORD_LENGTH = 5
        self.MAX_GUESSES = 6
        self.stats_file = stats_file
        self.stats = self._load_stats()

        self.settings = load_settings()

        self.word_bank, self.target_word = [], ""
        self.guesses, self.results, self.current_guess = [], [], ""
        self.game_over, self.win = False, False
        self.current_mode = 'classic'
        self.message, self.message_timer = "", 0
        self.keyboard_colors = {chr(c): "KEY_DEFAULT" for c in range(ord('a'), ord('z') + 1)}

        # ✅ SOUND SYSTEM -------------------------------------------------
        self.sounds = {}
        sound_files = {
            "win": os.path.join("sounds", "win.mp3"),
            "lose": os.path.join("sounds", "lose.mp3"),
            "bg": os.path.join("sounds", "bg_music.mp3"),
            "type": os.path.join("sounds", "type.wav")
        }

        for name, path in sound_files.items():
            if name == "bg":
                continue
            try:
                self.sounds[name] = pygame.mixer.Sound(path)
            except Exception as e:
                print(f" Could not load sound {path}: {e}")
                self.sounds[name] = None

        bg_path = sound_files.get("bg")
        try:
            if bg_path and os.path.exists(bg_path):
                pygame.mixer.music.load(bg_path)
        except Exception as e:
            print(f" Could not load bg music {bg_path}: {e}")

        bg_vol = self.settings.get("bg_volume", DEFAULT_SETTINGS["bg_volume"])
        fx_vol = self.settings.get("fx_volume", DEFAULT_SETTINGS["fx_volume"])
        try:
            pygame.mixer.music.set_volume(bg_vol)
        except Exception:
            pass
        for sname in ("win", "lose", "type"):
            if self.sounds.get(sname):
                self.sounds[sname].set_volume(fx_vol)
        if self.settings.get("sound_enabled", True):
            try:
                pygame.mixer.music.play(-1)
            except Exception:
                pass

    # ✅ Sound helper
    def play_sound(self, name):
        if name in self.sounds and self.sounds[name]:
            self.sounds[name].play()

    # ...existing code...
    def reset_game_state(self):
        self.guesses, self.results, self.current_guess = [], [], ""
        self.game_over, self.win = False, False
        self.message = ""
        self.keyboard_colors = {chr(c): "KEY_DEFAULT" for c in range(ord('a'), ord('z') + 1)}
    # ไม่ต้องรีเซ็ตเพลง bg
    # pygame.mixer.stop()
    # if self.sounds.get("bg"):
    #     self.sounds["bg"].play(-1)

    # <-- INSERT: set_message helper so handle_enter can call it
    def set_message(self, text, color_name="BLACK"):
        """Set in-game temporary message and timestamp. color_name is key in COLORS or an RGB tuple."""
        if isinstance(color_name, str):
            color = COLORS.get(color_name, COLORS["BLACK"])
        else:
            color = color_name
        self.message = (text, color)
        self.message_timer = pygame.time.get_ticks()
# ...existing code...

    # ----------------------------------------------------------------
    # GAME LOGIC (unchanged)
    # ----------------------------------------------------------------
    def _load_words_from_file(self, filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                words = [line.strip().lower() for line in f if len(line.strip()) == self.WORD_LENGTH and line.strip().isalpha()]
            if not words:
                self.word_bank = ['apple', 'train', 'audio', 'house', 'world']
            else:
                self.word_bank = words
        except FileNotFoundError:
            self.word_bank = ['apple', 'train', 'audio', 'house', 'world']
            with open(filename, 'w', encoding='utf-8') as f:
                pass

    def _load_stats(self):
        if not os.path.exists(self.stats_file):
            return {"played": 0, "wins": 0, "current_streak": 0, "max_streak": 0, "guess_dist": {}}
        try:
            with open(self.stats_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {"played": 0, "wins": 0, "current_streak": 0, "max_streak": 0, "guess_dist": {}}

    def _save_stats(self):
        with open(self.stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, ensure_ascii=False, indent=4)

    def update_stats(self):
        self.stats["played"] += 1
        if self.win:
            self.stats["wins"] += 1
            self.stats["current_streak"] += 1
            self.stats["max_streak"] = max(self.stats["max_streak"], self.stats["current_streak"])
            guess_count = str(len(self.guesses))
            self.stats["guess_dist"][guess_count] = self.stats["guess_dist"].get(guess_count, 0) + 1
        else:
            self.stats["current_streak"] = 0
        self._save_stats()

    def check_guess(self, guess):
        result = ["GRAY"] * self.WORD_LENGTH
        target_counts = Counter(self.target_word)
        for i, letter in enumerate(guess):
            if letter == self.target_word[i]:
                result[i] = "GREEN"
                target_counts[letter] -= 1
        for i, letter in enumerate(guess):
            if result[i] != "GREEN" and letter in target_counts and target_counts[letter] > 0:
                result[i] = "YELLOW"
                target_counts[letter] -= 1
        for i, letter in enumerate(guess):
            if 'a' <= letter <= 'z':
                if result[i] == "GREEN":
                    self.keyboard_colors[letter] = "GREEN"
                elif result[i] == "YELLOW" and self.keyboard_colors[letter] != "GREEN":
                    self.keyboard_colors[letter] = "YELLOW"
                elif self.keyboard_colors[letter] == "KEY_DEFAULT":
                    self.keyboard_colors[letter] = "KEY_USED"
        return result

    def is_valid_guess(self, guess):
        if len(guess) != self.WORD_LENGTH:
            self.set_message(f"Guess must be {self.WORD_LENGTH} letters", "RED")
            return False
        return True

    def handle_enter(self):
        if self.game_over:
            return
        if self.is_valid_guess(self.current_guess):
            self.guesses.append(self.current_guess)
            self.results.append(self.check_guess(self.current_guess))
            self.current_guess = ""
            
            if self.guesses[-1] == self.target_word:
                self.win = self.game_over = True
                self.set_message("YOU WIN", "GREEN")

                # render immediate end-screen so message appears BEFORE SFX
                try:
                    SCREEN.fill(COLORS["LIGHT_GRAY"])
                    self.draw_header(SCREEN)
                    self.draw_board(SCREEN)
                    self.draw_keyboard(SCREEN)
                    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                    overlay.fill((211, 211, 211, 180))
                    SCREEN.blit(overlay, (0, 0))
                    end_text_str, color = self.message
                    end_text_surf = FONTS["end_game"].render(end_text_str, True, color)
                    SCREEN.blit(end_text_surf, end_text_surf.get_rect(center=(WIDTH / 2, HEIGHT / 2 - 30)))
                    prompt_surf = FONTS["message"].render("Press Enter to return to menu", True, COLORS["BLACK"])
                    SCREEN.blit(prompt_surf, prompt_surf.get_rect(center=(WIDTH / 2, HEIGHT - 50)))
                    self.draw_settings_gear(SCREEN)
                    pygame.display.flip()
                except Exception:
                    pass

                # short pause so player sees message
                pygame.time.wait(250)

                # pause bg, play win SFX, then resume bg if enabled (from same pos if possible)
                try:
                    bg_pos = pygame.mixer.music.get_pos()
                    pygame.mixer.music.stop()
                except Exception:
                    bg_pos = None
                if self.sounds.get("win"):
                    self.sounds["win"].play()
                    pygame.time.wait(int(self.sounds["win"].get_length() * 1000))
                if self.settings.get("sound_enabled", True):
                    try:
                        if bg_pos is not None and bg_pos >= 0:
                            pygame.mixer.music.play(-1, bg_pos / 1000.0)
                        else:
                            pygame.mixer.music.play(-1)
                    except Exception:
                        try:
                            pygame.mixer.music.play(-1)
                        except Exception:
                            pass
                if self.current_mode != 'unlimited':
                    self.update_stats()

            elif len(self.guesses) == self.MAX_GUESSES:
                self.game_over = True
                self.set_message("LOSE", "RED")

                # render immediate end-screen so message appears BEFORE SFX
                try:
                    SCREEN.fill(COLORS["LIGHT_GRAY"])
                    self.draw_header(SCREEN)
                    self.draw_board(SCREEN)
                    self.draw_keyboard(SCREEN)
                    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                    overlay.fill((211, 211, 211, 180))
                    SCREEN.blit(overlay, (0, 0))
                    end_text_str, color = self.message
                    end_text_surf = FONTS["end_game"].render(end_text_str, True, color)
                    SCREEN.blit(end_text_surf, end_text_surf.get_rect(center=(WIDTH / 2, HEIGHT / 2 - 30)))
                    answer_surf = FONTS["message"].render(f"The word was: {self.target_word.upper()}", True, COLORS["BLACK"])
                    SCREEN.blit(answer_surf, answer_surf.get_rect(center=(WIDTH / 2, HEIGHT / 2 + 15)))
                    prompt_surf = FONTS["message"].render("Press Enter to return to menu", True, COLORS["BLACK"])
                    SCREEN.blit(prompt_surf, prompt_surf.get_rect(center=(WIDTH / 2, HEIGHT - 50)))
                    self.draw_settings_gear(SCREEN)
                    pygame.display.flip()
                except Exception:
                    pass

                # short pause so player sees message
                pygame.time.wait(250)

                # pause bg, play lose SFX, then resume bg if enabled
                try:
                    bg_pos = pygame.mixer.music.get_pos()
                    pygame.mixer.music.stop()
                except Exception:
                    bg_pos = None
                if self.sounds.get("lose"):
                    self.sounds["lose"].play()
                    pygame.time.wait(int(self.sounds["lose"].get_length() * 1000))
                if self.settings.get("sound_enabled", True):
                    try:
                        if bg_pos is not None and bg_pos >= 0:
                            pygame.mixer.music.play(-1, bg_pos / 1000.0)
                        else:
                            pygame.mixer.music.play(-1)
                    except Exception:
                        try:
                            pygame.mixer.music.play(-1)
                        except Exception:
                            pass
                if self.current_mode != 'unlimited':
                    self.update_stats()

    # ----------------------------------------------------------------
    # DRAWING
    # ----------------------------------------------------------------
    def draw_board(self, surface):
        width, height = surface.get_size()
        board_area_h = height * 0.5
        box_size = min((width * 0.65) / self.WORD_LENGTH, board_area_h / self.MAX_GUESSES)
        padding = box_size * 0.1
        grid_width = (box_size * self.WORD_LENGTH) + (padding * (self.WORD_LENGTH - 1))
        start_x, start_y = (width - grid_width) / 2, height * 0.08

        rows_to_display = len(self.guesses) + 1
        if self.game_over:
            rows_to_display = len(self.guesses)
        rows_to_display = min(rows_to_display, self.MAX_GUESSES)

        for i in range(rows_to_display):
            for j in range(self.WORD_LENGTH):
                box = pygame.Rect(start_x + j * (box_size + padding), start_y + i * (box_size + padding), box_size, box_size)
                letter, color_key, l_color = "", "WHITE", COLORS["BLACK"]
                if i < len(self.guesses):
                    letter, color_key, l_color = self.guesses[i][j], self.results[i][j], COLORS["WHITE"]
                elif i == len(self.guesses) and j < len(self.current_guess):
                    letter = self.current_guess[j]
                pygame.draw.rect(surface, COLORS[color_key], box, border_radius=5)
                if color_key == "WHITE":
                    pygame.draw.rect(surface, COLORS["GRAY"], box, 2, border_radius=5)
                if letter:
                    text_surf = FONTS["letter"].render(letter.upper(), True, l_color)
                    surface.blit(text_surf, text_surf.get_rect(center=box.center))

    def draw_keyboard(self, surface):
        width, height = surface.get_size()
        keys = ["qwertyuiop", "asdfghjkl", "zxcvbnm"]
        key_h = height * 0.045
        key_w = min(width * 0.06, key_h * 1.3)
        padding = key_w * 0.15
        start_y = height * 0.65
        for i, row in enumerate(keys):
            row_width = len(row) * (key_w + padding) - padding
            start_x = (width - row_width) / 2
            for j, char in enumerate(row):
                key_rect = pygame.Rect(start_x + j * (key_w + padding), start_y + i * (key_h + padding * 0.8), key_w, key_h)
                color_name = self.keyboard_colors[char]
                pygame.draw.rect(surface, COLORS[color_name], key_rect, border_radius=5)
                key_text = FONTS["key"].render(char.upper(), True, COLORS["WHITE"])
                surface.blit(key_text, key_text.get_rect(center=key_rect.center))

    def draw_header(self, surface):
        width, height = surface.get_size()
        mode_text = f"Mode: {self.current_mode.capitalize()}"
        title_text = FONTS["menu"].render(mode_text, True, COLORS["BLACK"])
        surface.blit(title_text, title_text.get_rect(center=(width / 2, height * 0.04)))

    def draw_settings_gear(self, surface):
        """Draw setting image (or gear fallback) at bottom-left and return its rect."""
        width, height = surface.get_size()
        margin = 10
        gear_size = int(min(width, height) * 0.06)

        if SETTING_IMG:
            try:
                img = pygame.transform.smoothscale(SETTING_IMG, (gear_size, gear_size))
            except Exception:
                img = SETTING_IMG
            rect = img.get_rect()
            rect.bottomleft = (margin, height - margin)
            surface.blit(img, rect)
            return rect
        else:
            # fallback: วาดไอคอนฟอนต์
            gear_surf = FONTS["menu"].render("⚙", True, COLORS["BLACK"])
            gear_rect = gear_surf.get_rect()
            gear_rect.bottomleft = (margin, height - margin)
            surface.blit(gear_surf, gear_rect)
            return gear_rect
    
    def draw_message(self, surface):
        width, height = surface.get_size()
        if self.message and pygame.time.get_ticks() - self.message_timer < 2000 and not self.game_over:
            text, color = self.message
            msg_surface = FONTS["message"].render(text, True, color)
            surface.blit(msg_surface, msg_surface.get_rect(center=(width / 2, height * 0.95)))

    def start_new_game(self, mode):
        file_map = {'classic': 'words_medium.txt', 'unlimited': 'words_easy.txt', 'hard': 'words_hard.txt'}
        filename = file_map.get(mode, 'words_medium.txt')
        self._load_words_from_file(filename)
        self.reset_game_state()
        self.current_mode = mode
        self.target_word = random.choice(self.word_bank)
        print(f"Starting {mode} mode. Hint: {self.target_word}")
        return True

    def run_game(self):
        global SCREEN, WIDTH, HEIGHT
        running = True
        clock = pygame.time.Clock()
        while running:
            # prepare gear rect for click detection
            gear_rect_for_events = pygame.Rect(10, HEIGHT - int(min(WIDTH, HEIGHT) * 0.06) - 10,
                                               int(min(WIDTH, HEIGHT) * 0.06), int(min(WIDTH, HEIGHT) * 0.06))

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.VIDEORESIZE:
                    WIDTH, HEIGHT = max(event.w, 500), max(event.h, 750)
                    SCREEN = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
                    update_fonts(WIDTH, HEIGHT)
                if event.type == pygame.MOUSEBUTTONDOWN:
                    # open settings when gear clicked
                    if gear_rect_for_events.collidepoint(event.pos):
                        settings_menu(self)
                        continue
                if event.type == pygame.KEYDOWN:
                    if self.game_over:
                        if event.key in [pygame.K_RETURN, pygame.K_ESCAPE]:
                            running = False
                        continue
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_BACKSPACE:
                        self.current_guess = self.current_guess[:-1]
                    elif event.key == pygame.K_RETURN and len(self.current_guess) == self.WORD_LENGTH:
                        self.handle_enter()
                    elif 'a' <= event.unicode.lower() <= 'z' and len(self.current_guess) < self.WORD_LENGTH:
                        self.current_guess += event.unicode.lower()
                        self.play_sound("type")  # ✅ เสียงพิมพ์

            SCREEN.fill(COLORS["LIGHT_GRAY"])
            self.draw_header(SCREEN)
            self.draw_board(SCREEN)
            self.draw_keyboard(SCREEN)
            self.draw_message(SCREEN)

            # draw gear icon (bottom-left)
            self.draw_settings_gear(SCREEN)

            if self.game_over:
                overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                overlay.fill((211, 211, 211, 180))
                SCREEN.blit(overlay, (0, 0))
                end_text_str, color = self.message
                end_text_surf = FONTS["end_game"].render(end_text_str, True, color)
                SCREEN.blit(end_text_surf, end_text_surf.get_rect(center=(WIDTH / 2, HEIGHT / 2 - 30)))
                if not self.win:
                    answer_surf = FONTS["message"].render(f"The word was: {self.target_word.upper()}", True, COLORS["BLACK"])
                    SCREEN.blit(answer_surf, answer_surf.get_rect(center=(WIDTH / 2, HEIGHT / 2 + 15)))
                prompt_surf = FONTS["message"].render("Press Enter to return to menu", True, COLORS["BLACK"])
                SCREEN.blit(prompt_surf, prompt_surf.get_rect(center=(WIDTH / 2, HEIGHT - 50)))

            pygame.display.flip()
            clock.tick(60)
#ตั้งค่า 
class VolumeSlider:
    def __init__(self, x, y, width, height, initial_value=0.5):
        self.rect = pygame.Rect(x, y, width, height)
        self.knob = pygame.Rect(x, y, 20, height)
        self.value = initial_value
        self.active = False
        self.update_knob_position()
    
    def update_knob_position(self):
        self.knob.centerx = self.rect.left + (self.rect.width * self.value)
        self.knob.centery = self.rect.centery
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.knob.collidepoint(event.pos):
                self.active = True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.active = False
        elif event.type == pygame.MOUSEMOTION and self.active:
            rel_x = min(max(event.pos[0], self.rect.left), self.rect.right)
            self.value = (rel_x - self.rect.left) / self.rect.width
            self.update_knob_position()
    
    def draw(self, surface):
        pygame.draw.rect(surface, COLORS["GRAY"], self.rect, border_radius=5)
        pygame.draw.rect(surface, COLORS["BLACK"], self.knob, border_radius=5)
def settings_menu(game):
    global SCREEN, WIDTH, HEIGHT
    settings_running = True
    
    # current settings (live)
    sound_enabled = bool(game.settings.get("sound_enabled", True))
    bg_slider_val = float(game.settings.get("bg_volume", DEFAULT_SETTINGS["bg_volume"]))
    fx_slider_val = float(game.settings.get("fx_volume", DEFAULT_SETTINGS["fx_volume"]))

    # sliders
    slider_width = WIDTH * 0.4
    slider_height = HEIGHT * 0.03
    bg_slider = VolumeSlider(WIDTH * 0.45, HEIGHT * 0.35, slider_width, slider_height, bg_slider_val)
    fx_slider = VolumeSlider(WIDTH * 0.45, HEIGHT * 0.5, slider_width, slider_height, fx_slider_val)

    prev_bg = bg_slider.value
    prev_fx = fx_slider.value
    prev_enabled = sound_enabled

    # apply current volumes immediately (respecting enabled flag)
    try:
        pygame.mixer.music.set_volume(bg_slider.value)
    except Exception:
        pass
    for sname in ("win", "lose", "type"):
        if game.sounds.get(sname):
            game.sounds[sname].set_volume(fx_slider.value)
    if not sound_enabled:
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass
    else:
        try:
            if pygame.mixer.music.get_busy() is False:
                pygame.mixer.music.play(-1)
        except Exception:
            pass

    while settings_running:
        SCREEN.fill(COLORS["LIGHT_GRAY"])
        
        # Title
        title = FONTS["menu"].render("Sound Settings", True, COLORS["BLACK"])
        SCREEN.blit(title, title.get_rect(center=(WIDTH * 0.5, HEIGHT * 0.1)))

        # Toggle sound button
        sound_text = "Sound: ON" if sound_enabled else "Sound: OFF"
        sound_button = pygame.Rect(WIDTH * 0.3, HEIGHT * 0.2, WIDTH * 0.4, HEIGHT * 0.08)
        pygame.draw.rect(SCREEN, COLORS["WHITE"], sound_button, border_radius=10)
        pygame.draw.rect(SCREEN, COLORS["BLACK"], sound_button, 2, border_radius=10)
        sound_text_surf = FONTS["stats"].render(sound_text, True, COLORS["BLACK"])
        SCREEN.blit(sound_text_surf, sound_text_surf.get_rect(center=sound_button.center))

        # Volume labels
        bg_label = FONTS["stats"].render("Background Music", True, COLORS["BLACK"])
        fx_label = FONTS["stats"].render("Sound Effects", True, COLORS["BLACK"])
        SCREEN.blit(bg_label, (WIDTH * 0.15, HEIGHT * 0.35))
        SCREEN.blit(fx_label, (WIDTH * 0.15, HEIGHT * 0.5))

        # Draw sliders
        bg_slider.draw(SCREEN)
        fx_slider.draw(SCREEN)

        # Back button
        back_button = pygame.Rect(WIDTH * 0.3, HEIGHT * 0.8, WIDTH * 0.4, HEIGHT * 0.08)
        pygame.draw.rect(SCREEN, COLORS["WHITE"], back_button, border_radius=10)
        pygame.draw.rect(SCREEN, COLORS["BLACK"], back_button, 2, border_radius=10)
        back_text = FONTS["menu"].render("Back", True, COLORS["BLACK"])
        SCREEN.blit(back_text, back_text.get_rect(center=back_button.center))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # ensure settings saved before quit
                game.settings["bg_volume"] = bg_slider.value
                game.settings["fx_volume"] = fx_slider.value
                game.settings["sound_enabled"] = sound_enabled
                save_settings(game.settings)
                pygame.quit()
                sys.exit()
            if event.type == pygame.VIDEORESIZE:
                WIDTH, HEIGHT = max(event.w, 500), max(event.h, 750)
                SCREEN = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
                update_fonts(WIDTH, HEIGHT)
            if event.type == pygame.MOUSEBUTTONDOWN:
                if sound_button.collidepoint(event.pos):
                    # toggle sound enabled
                    sound_enabled = not sound_enabled
                    game.settings["sound_enabled"] = sound_enabled
                    if sound_enabled:
                        # resume bg with saved bg volume
                        try:
                            pygame.mixer.music.set_volume(bg_slider.value)
                            pygame.mixer.music.play(-1)
                        except Exception:
                            pass
                    else:
                        try:
                            pygame.mixer.music.stop()
                        except Exception:
                            pass
                    save_settings(game.settings)
                    prev_enabled = sound_enabled
                elif back_button.collidepoint(event.pos):
                    # save and exit settings
                    game.settings["bg_volume"] = bg_slider.value
                    game.settings["fx_volume"] = fx_slider.value
                    game.settings["sound_enabled"] = sound_enabled
                    # apply to mixers
                    try:
                        pygame.mixer.music.set_volume(bg_slider.value)
                        if sound_enabled and pygame.mixer.music.get_busy() is False:
                            pygame.mixer.music.play(-1)
                        elif not sound_enabled:
                            pygame.mixer.music.stop()
                    except Exception:
                        pass
                    for sname in ("win", "lose", "type"):
                        if game.sounds.get(sname):
                            game.sounds[sname].set_volume(fx_slider.value)
                    save_settings(game.settings)
                    settings_running = False

            # pass events to sliders
            bg_slider.handle_event(event)
            fx_slider.handle_event(event)

        # live update volumes and persist if changed
        changed = False
        if bg_slider.value != prev_bg:
            prev_bg = bg_slider.value
            game.settings["bg_volume"] = bg_slider.value
            try:
                pygame.mixer.music.set_volume(bg_slider.value)
            except Exception:
                pass
            changed = True
        if fx_slider.value != prev_fx:
            prev_fx = fx_slider.value
            game.settings["fx_volume"] = fx_slider.value
            for sname in ("win", "lose", "type"):
                if game.sounds.get(sname):
                    game.sounds[sname].set_volume(fx_slider.value)
            changed = True
        # If user toggled via other means, ensure saved (handled when clicked)
        if changed:
            save_settings(game.settings)

        pygame.display.flip()

    # ...existing code...
def display_stats(stats):
    """Simple stats screen — shows basic stats and guess distribution, Back button returns to menu."""
    global SCREEN, WIDTH, HEIGHT
    running = True
    while running:
        SCREEN.fill(COLORS["LIGHT_GRAY"])

        # Title
        title = FONTS["menu"].render("Statistics", True, COLORS["BLACK"])
        SCREEN.blit(title, title.get_rect(center=(WIDTH * 0.5, HEIGHT * 0.08)))

        # Basic stats
        played_s = FONTS["stats"].render(f"Played: {stats.get('played', 0)}", True, COLORS["BLACK"])
        wins_s = FONTS["stats"].render(f"Wins: {stats.get('wins', 0)}", True, COLORS["BLACK"])
        streak_s = FONTS["stats"].render(f"Current Streak: {stats.get('current_streak', 0)}", True, COLORS["BLACK"])
        max_s = FONTS["stats"].render(f"Max Streak: {stats.get('max_streak', 0)}", True, COLORS["BLACK"])

        SCREEN.blit(played_s, (WIDTH * 0.12, HEIGHT * 0.18))
        SCREEN.blit(wins_s, (WIDTH * 0.12, HEIGHT * 0.24))
        SCREEN.blit(streak_s, (WIDTH * 0.12, HEIGHT * 0.30))
        SCREEN.blit(max_s, (WIDTH * 0.12, HEIGHT * 0.36))

        # Guess distribution
        dist_title = FONTS["stats"].render("Guess Distribution:", True, COLORS["BLACK"])
        SCREEN.blit(dist_title, (WIDTH * 0.12, HEIGHT * 0.44))
        guess_dist = stats.get("guess_dist", {})
        # show up to 6 guesses lines
        for i in range(1, 7):
            count = guess_dist.get(str(i), 0)
            line = FONTS["message"].render(f"{i}: {count}", True, COLORS["BLACK"])
            SCREEN.blit(line, (WIDTH * 0.18, HEIGHT * (0.44 + 0.06 * i)))

        # Back button
        back_button = pygame.Rect(WIDTH * 0.3, HEIGHT * 0.82, WIDTH * 0.4, HEIGHT * 0.08)
        pygame.draw.rect(SCREEN, COLORS["WHITE"], back_button, border_radius=10)
        pygame.draw.rect(SCREEN, COLORS["BLACK"], back_button, 2, border_radius=10)
        back_text = FONTS["menu"].render("Back", True, COLORS["BLACK"])
        SCREEN.blit(back_text, back_text.get_rect(center=back_button.center))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.VIDEORESIZE:
                WIDTH, HEIGHT = max(event.w, 500), max(event.h, 750)
                SCREEN = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
                update_fonts(WIDTH, HEIGHT)
            if event.type == pygame.MOUSEBUTTONDOWN:
                if back_button.collidepoint(event.pos):
                    running = False

        pygame.display.flip()
# ...existing code...
# ...existing code...
def main_menu():
    global SCREEN, WIDTH, HEIGHT
    game = WordleGamePygame()
    button_actions = {
        "Classic Mode": 'classic',
        "Unlimited Mode": 'unlimited',
        "Hard Mode": 'hard',
        "Settings": 'settings',
        "Statistics": 'stats',
        "Exit Game": 'exit'
    }
    button_keys = list(button_actions.keys())
    while True:
        SCREEN.fill(COLORS["LIGHT_GRAY"])
        title_text = FONTS["menu"].render("Wordle Game", True, COLORS["BLACK"])
        SCREEN.blit(title_text, title_text.get_rect(center=(WIDTH / 2, HEIGHT * 0.15)))

        buttons = {}
        button_h, button_w = HEIGHT * 0.08, WIDTH * 0.7
        for i, text in enumerate(button_keys):
            rect = pygame.Rect((WIDTH - button_w) / 2, HEIGHT * 0.3 + i * (button_h * 1.2), button_w, button_h)
            buttons[text] = rect
            pygame.draw.rect(SCREEN, COLORS["WHITE"], rect, border_radius=10)
            pygame.draw.rect(SCREEN, COLORS["BLACK"], rect, 2, border_radius=10)
            btn_text = FONTS["stats"].render(text, True, COLORS["BLACK"])
            SCREEN.blit(btn_text, btn_text.get_rect(center=rect.center))

        # draw gear icon using class method and get clickable rect
        gear_rect = game.draw_settings_gear(SCREEN)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.VIDEORESIZE:
                WIDTH, HEIGHT = max(event.w, 500), max(event.h, 750)
                SCREEN = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
                update_fonts(WIDTH, HEIGHT)
            if event.type == pygame.MOUSEBUTTONDOWN:
                # gear click opens settings
                if gear_rect.collidepoint(event.pos):
                    settings_menu(game)
                    continue
                for text, rect in buttons.items():
                    if rect.collidepoint(event.pos):
                        action = button_actions[text]
                        if action in ['classic', 'unlimited', 'hard']:
                            if game.start_new_game(action):
                                game.run_game()
                        elif action == 'settings':
                            settings_menu(game)
                        elif action == 'stats':
                            display_stats(game.stats)
                        elif action == 'exit':
                            pygame.quit()
                            sys.exit()

        pygame.display.flip()

if __name__ == "__main__":
    main_menu()