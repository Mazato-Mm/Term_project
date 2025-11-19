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

def load_image(filename, use_convert_alpha=True):
    path = os.path.join(os.path.dirname(__file__), filename)
    try:
        image = pygame.image.load(path)
        if use_convert_alpha:
            return image.convert_alpha()
        return image
    except Exception as e:
        print(f"Could not load image {filename}: {e}")
        return None

try:
    icon = load_image("icon.png", use_convert_alpha=False)
    if icon:
        pygame.display.set_icon(icon)
except Exception as e:
    print(f"Could not set icon: {e}")

SETTING_IMG = load_image("setting_image.jpg")
RETURN_IMG = load_image("return_image.png")

BG_COLOR = (35, 65, 150)
BUTTON_COLOR = (80, 150, 255)
BUTTON_HOVER = (130, 180, 255)
TEXT_COLOR = (255, 255, 255)

GREEN = (106, 170, 100)
YELLOW = (201, 180, 88)
KEY_GRAY = (120, 124, 126)
RED = (200, 70, 70)

COLORS = {
    "WHITE": TEXT_COLOR, 
    "BLACK": (0, 0, 0),
    "GREEN": GREEN, 
    "YELLOW": YELLOW,
    "GRAY": KEY_GRAY,
    "LIGHT_GRAY": (200, 200, 200),
    "KEY_DEFAULT": BUTTON_COLOR,
    "KEY_USED": KEY_GRAY,
    "RED": RED
}

def load_settings(path=SETTINGS_FILE):
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {
                    "sound_enabled": bool(data.get("sound_enabled", True)),
                    "bg_volume": float(data.get("bg_volume", DEFAULT_SETTINGS["bg_volume"])),
                    "fx_volume": float(data.get("fx_volume", DEFAULT_SETTINGS["fx_volume"]))
                }
    except Exception as e:
        print(f"Could not load settings: {e}")
    save_settings(DEFAULT_SETTINGS, path) 
    return DEFAULT_SETTINGS.copy()

def save_settings(settings, path=SETTINGS_FILE):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Could not save settings: {e}")

def get_font(size):
    for f in ["Poppins-Regular.ttf", "Montserrat-Regular.ttf", "Kanit-Regular.ttf"]:
        if os.path.exists(f):
            return pygame.font.Font(f, size)
    return pygame.font.SysFont("segoeui", size, bold=True)

FONTS = {}
def update_fonts(width, height):
    base_size = min(width, height)
    try:
        FONTS["letter"] = get_font(int(base_size * 0.055))
        FONTS["menu"] = get_font(int(base_size * 0.05))
        FONTS["stats"] = get_font(int(base_size * 0.036))
        FONTS["message"] = get_font(int(base_size * 0.03))
        FONTS["key"] = get_font(int(base_size * 0.023))
        FONTS["end_game"] = get_font(int(base_size * 0.06))
        FONTS["button"] = get_font(int(base_size * 0.04))
    except Exception as e:
        print(f"Error loading fonts: {e}")
        for key, size in {"letter": 0.07, "menu": 0.06, "stats": 0.04, "message": 0.035, "key": 0.03, "end_game": 0.07, "button": 0.05}.items():
            FONTS[key] = pygame.font.Font(None, int(base_size * size))

update_fonts(WIDTH, HEIGHT) 

def draw_button(screen, rect, text, mx, my, font):
    is_hover = rect.collidepoint((mx, my))
    color = BUTTON_HOVER if is_hover else BUTTON_COLOR
    pygame.draw.rect(screen, color, rect, border_radius=20)
    pygame.draw.rect(screen, TEXT_COLOR, rect, 3, border_radius=20) 
    label = font.render(text, True, TEXT_COLOR)
    label_rect = label.get_rect(center=rect.center)
    screen.blit(label, label_rect)

def draw_title(screen, w, text, y=100):
    y_pos = int(HEIGHT * (y / 750)) 
    font_size = max(28, min(64, w // 14))
    title_font = get_font(font_size)
    label = title_font.render(text, True, TEXT_COLOR)
    label_rect = label.get_rect(center=(w // 2, y_pos))
    screen.blit(label, label_rect)

def draw_menu_buttons(screen, mx, my, button_texts, start_y_ratio, font):
    buttons = {}
    button_h, button_w = HEIGHT * 0.08, WIDTH * 0.7
    start_y = HEIGHT * start_y_ratio
    
    for i, text in enumerate(button_texts):
        y_pos = start_y + i * (button_h * 1.2)
        if text == "Back": 
             y_pos += button_h * 0.3
             
        rect = pygame.Rect((WIDTH - button_w) / 2, y_pos, button_w, button_h)
        buttons[text] = rect
        draw_button(screen, rect, text, mx, my, font)
    return buttons

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
        self.key_rects = {} 
        self.sounds = {}

        self.timer_start_time = 0
        self.time_limit = 30000 
        self.time_remaining = 30.0 

        def load_sound(path):
            try:
                return pygame.mixer.Sound(path)
            except Exception as e:
                print(f"Could not load sound {path}: {e}")
                return None

        self.sounds = {
            "win": load_sound(os.path.join("sounds", "win.mp3")),
            "lose": load_sound(os.path.join("sounds", "lose.mp3")),
            "type": load_sound(os.path.join("sounds", "type.wav"))
        }
        
        try:
            pygame.mixer.music.load(os.path.join("sounds", "bg_music.mp3"))
        except Exception as e:
            print(f"Could not load bg music: {e}")

        self.apply_volume_settings()
        
        if self.settings.get("sound_enabled", True):
            try:
                pygame.mixer.music.play(-1)
            except Exception: pass

    def apply_volume_settings(self):
        bg_vol = self.settings.get("bg_volume", DEFAULT_SETTINGS["bg_volume"])
        fx_vol = self.settings.get("fx_volume", DEFAULT_SETTINGS["fx_volume"])
        try:
            pygame.mixer.music.set_volume(bg_vol)
        except Exception: pass
        for sname in ("win", "lose", "type"):
            if self.sounds.get(sname):
                self.sounds[sname].set_volume(fx_vol)

    def play_sound(self, name):
        if self.settings.get("sound_enabled", True) and name in self.sounds and self.sounds[name]:
            self.sounds[name].play()

    def reset_game_state(self):
        self.guesses, self.results, self.current_guess = [], [], ""
        self.game_over, self.win = False, False
        self.message = ""
        self.keyboard_colors = {chr(c): "KEY_DEFAULT" for c in range(ord('a'), ord('z') + 1)}
        self.key_rects = {} 
        self.timer_start_time = 0
        self.time_remaining = 30.0

    def set_message(self, text, color_name="WHITE"):
        if isinstance(color_name, str):
            color = COLORS.get(color_name, COLORS["WHITE"])
        else:
            color = color_name
        self.message = (text, color)
        self.message_timer = pygame.time.get_ticks()

    def _load_words_from_file(self, filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                words = [line.strip().lower() for line in f if len(line.strip()) == self.WORD_LENGTH and line.strip().isalpha()]
            if not words:
                print(f"Warning: Word file '{filename}' is empty or invalid. Using default list.")
                self.word_bank = ['apple', 'train', 'audio', 'house', 'world']
            else:
                self.word_bank = words
        except FileNotFoundError:
            print(f"Warning: Word file '{filename}' not found. Using default list and creating file.")
            self.word_bank = ['apple', 'train', 'audio', 'house', 'world']
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    pass 
            except Exception as e:
                print(f"Could not create file {filename}: {e}")

    def _load_stats(self):
        if not os.path.exists(self.stats_file):
            return {"played": 0, "wins": 0, "current_streak": 0, "max_streak": 0, "guess_dist": {}}
        try:
            with open(self.stats_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {"played": 0, "wins": 0, "current_streak": 0, "max_streak": 0, "guess_dist": {}}

    def _save_stats(self):
        try:
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Could not save stats: {e}")

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

    def _render_end_screen(self):
        try:
            SCREEN.fill(BG_COLOR) 
            
            end_text_str, color = self.message
            
            if self.win and self.current_mode == 'unlimited':
                guess_count = len(self.guesses)
                end_text_str = f"YOU WIN! ({guess_count} guesses)"
            
            end_text_surf = FONTS["end_game"].render(end_text_str, True, color)
            SCREEN.blit(end_text_surf, end_text_surf.get_rect(center=(WIDTH / 2, HEIGHT / 2 - 30)))
            
            if not self.win:
                answer_surf = FONTS["message"].render(f"The word was: {self.target_word.upper()}", True, COLORS["WHITE"])
                SCREEN.blit(answer_surf, answer_surf.get_rect(center=(WIDTH / 2, HEIGHT / 2 + 15)))
                
            prompt_surf = FONTS["message"].render("Press Enter to return to menu", True, COLORS["WHITE"])
            SCREEN.blit(prompt_surf, prompt_surf.get_rect(center=(WIDTH / 2, HEIGHT - 50)))
            
            pygame.display.flip() 
        except Exception as e:
            print(f"Error rendering end screen: {e}")

    def _handle_end_game_sfx(self, sound_name):
        try:
            bg_pos = pygame.mixer.music.get_pos() 
            pygame.mixer.music.stop()
        except Exception:
            bg_pos = None
            
        if self.settings.get("sound_enabled", True) and self.sounds.get(sound_name):
            self.sounds[sound_name].play()
            pygame.time.wait(int(self.sounds[sound_name].get_length() * 1000))
        
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
                
                self._render_end_screen() 
                pygame.time.wait(250)     
                self._handle_end_game_sfx("win") 
                
                if self.current_mode != 'unlimited':
                    self.update_stats()

            elif len(self.guesses) == self.MAX_GUESSES and self.current_mode != 'unlimited':
                self.game_over = True
                self.set_message("LOSE", "RED")
                
                self._render_end_screen() 
                pygame.time.wait(250)     
                self._handle_end_game_sfx("lose") 
                
                if self.current_mode != 'unlimited':
                    self.update_stats()

    def draw_board(self, surface):
        width, height = surface.get_size()
        
        board_area_h = height * 0.5
        padding_ratio = 0.1 
        grid_width_ratio = self.WORD_LENGTH + (self.WORD_LENGTH - 1) * padding_ratio
        box_size_w = (width * 0.8) / grid_width_ratio 
        
        grid_height_ratio = self.MAX_GUESSES + (self.MAX_GUESSES - 1) * padding_ratio
        box_size_h = board_area_h / grid_height_ratio
        
        box_size = min(box_size_w, box_size_h, 80) 
        padding = box_size * padding_ratio
        
        grid_width = (box_size * self.WORD_LENGTH) + (padding * (self.WORD_LENGTH - 1))
        start_x = (width - grid_width) / 2
        start_y = height * 0.1 

        if self.current_mode == 'unlimited' and not self.game_over:
            guesses_to_show = self.guesses[-1:-6:-1] 
            results_to_show = self.results[-1:-6:-1]
            num_history_rows_to_show = min(len(self.guesses), 5)
            total_rows_to_draw = 1 + num_history_rows_to_show 

            for i in range(total_rows_to_draw): 
                y_pos = start_y + i * (box_size + padding)
                
                if i == 0: 
                    for j in range(self.WORD_LENGTH):
                        box = pygame.Rect(start_x + j * (box_size + padding), y_pos, box_size, box_size)
                        letter, l_color = "", COLORS["WHITE"]
                        
                        if j < len(self.current_guess):
                            letter = self.current_guess[j]
                            pygame.draw.rect(surface, COLORS["BLACK"], box, border_radius=5) 
                            pygame.draw.rect(surface, COLORS["GRAY"], box, 2, border_radius=5) 
                            l_color = COLORS["WHITE"] 
                        else:
                            pygame.draw.rect(surface, COLORS["BLACK"], box, border_radius=5) 
                            pygame.draw.rect(surface, COLORS["GRAY"], box, 2, border_radius=5) 

                        if letter:
                            text_surf = FONTS["letter"].render(letter.upper(), True, l_color)
                            surface.blit(text_surf, text_surf.get_rect(center=box.center))
                            
                else: 
                    guess_idx = i - 1 
                    guess = guesses_to_show[guess_idx]
                    result = results_to_show[guess_idx]
                    
                    for j in range(self.WORD_LENGTH):
                        box = pygame.Rect(start_x + j * (box_size + padding), y_pos, box_size, box_size)
                        letter, color_key, l_color = guess[j], result[j], COLORS["WHITE"]
                        pygame.draw.rect(surface, COLORS[color_key], box, border_radius=5)
                        
                        text_surf = FONTS["letter"].render(letter.upper(), True, l_color)
                        surface.blit(text_surf, text_surf.get_rect(center=box.center))
            return 

        for i in range(self.MAX_GUESSES): 
            for j in range(self.WORD_LENGTH):
                box = pygame.Rect(start_x + j * (box_size + padding), start_y + i * (box_size + padding), box_size, box_size)
                letter, color_key, l_color = "", "BLACK", COLORS["WHITE"] 
                
                if i < len(self.guesses): 
                    letter, color_key, l_color = self.guesses[i][j], self.results[i][j], COLORS["WHITE"]
                    pygame.draw.rect(surface, COLORS[color_key], box, border_radius=5)
                elif i == len(self.guesses) and j < len(self.current_guess) and not self.game_over: 
                    letter = self.current_guess[j]
                    pygame.draw.rect(surface, COLORS["BLACK"], box, border_radius=5) 
                    pygame.draw.rect(surface, COLORS["GRAY"], box, 2, border_radius=5) 
                    l_color = COLORS["WHITE"] 
                else: 
                    pygame.draw.rect(surface, COLORS["BLACK"], box, border_radius=5) 
                    pygame.draw.rect(surface, COLORS["GRAY"], box, 2, border_radius=5) 

                if letter:
                    text_surf = FONTS["letter"].render(letter.upper(), True, l_color)
                    surface.blit(text_surf, text_surf.get_rect(center=box.center))

    def draw_keyboard(self, surface): #โค้ดดังกล่าวทำงานได้สอดคล้องกับคำแนะนำที่ระบุไว้ในคอมเมนต์แล้วอย่างมีประสิทธิภาพ
        self.key_rects.clear() 
        width, height = surface.get_size()
        
        key_rows = [
            list("qwertyuiop"), 
            list("asdfghjkl"), 
            ["ENTER"] + list("zxcvbnm") + ["BACK"]
        ]
        
        keyboard_area_y = height * 0.25 
        key_h = (keyboard_area_y / 4) * 0.9 
        key_w = min(width * 0.08, key_h * 1.3) 
        padding = key_w * 0.15
        start_y = height * 0.7 

        for i, row in enumerate(key_rows):
            total_key_units = 0
            for key in row:
                total_key_units += 1 if len(key) == 1 else 1.5 
            
            row_width = (total_key_units * key_w) + ((len(row) - 1) * padding)
            current_x = (width - row_width) / 2
            current_y = start_y + i * (key_h + padding * 0.8)

            for key in row:
                current_key_w = key_w
                color_name = self.keyboard_colors.get(key, "KEY_DEFAULT") 
                
                if key == "ENTER" or key == "BACK":
                    current_key_w = key_w * 1.5
                    color_name = "KEY_DEFAULT"
                
                key_rect = pygame.Rect(current_x, current_y, current_key_w, key_h)
                self.key_rects[key] = key_rect 
                
                pygame.draw.rect(surface, COLORS[color_name], key_rect, border_radius=8)
                
                key_text_str = key.upper()
                if key == "BACK":
                    key_text_str = "<=" 
                
                key_text = FONTS["key"].render(key_text_str, True, COLORS["WHITE"])
                surface.blit(key_text, key_text.get_rect(center=key_rect.center))
                
                current_x += current_key_w + padding

    def draw_header(self, surface):
        width, height = surface.get_size()
        
        mode_text = f"Mode: {self.current_mode.replace('_', ' ').title()}"
        
        title_text = FONTS["menu"].render(mode_text, True, COLORS["WHITE"])
        surface.blit(title_text, title_text.get_rect(center=(width / 2, height * 0.04)))

        if self.current_mode == 'limited_time' and not self.game_over:
            timer_display = max(0, int(self.time_remaining + 0.99)) 
            timer_text = f"Time: {timer_display}"
            timer_color = COLORS["WHITE"] if self.time_remaining > 5 else COLORS["RED"]
            timer_surf = FONTS["stats"].render(timer_text, True, timer_color)
            timer_rect = timer_surf.get_rect(topright=(width - 20, height * 0.02))
            surface.blit(timer_surf, timer_rect)

    def draw_settings_gear(self, surface):
        width, height = surface.get_size()
        margin = 10
        gear_size = int(min(width, height) * 0.06)
        gear_rect = pygame.Rect(margin, height - gear_size - margin, gear_size, gear_size) 

        try:
            if not SETTING_IMG: raise ValueError("No setting image")
            img = pygame.transform.smoothscale(SETTING_IMG, (gear_size, gear_size))
            surface.blit(img, gear_rect)
        except Exception:
            gear_surf = FONTS["menu"].render("⚙", True, COLORS["WHITE"])
            surface.blit(gear_surf, gear_surf.get_rect(center=gear_rect.center))
        return gear_rect 
    
    def draw_return_button(self, surface):
        width, height = surface.get_size()
        margin = 10
        btn_size = int(min(width, height) * 0.06) 
        btn_rect = pygame.Rect(margin, margin, btn_size, btn_size) 

        try:
            if not RETURN_IMG: raise ValueError("No return image")
            img = pygame.transform.smoothscale(RETURN_IMG, (btn_size, btn_size))
            surface.blit(img, btn_rect)
        except Exception:
            fallback_text = FONTS["menu"].render("<-", True, COLORS["WHITE"])
            surface.blit(fallback_text, fallback_text.get_rect(center=btn_rect.center))
        return btn_rect
    
    def draw_message(self, surface):
        width, height = surface.get_size()
        if self.message and pygame.time.get_ticks() - self.message_timer < 2000 and not self.game_over:
            text, color = self.message
            msg_surface = FONTS["message"].render(text, True, color)
            surface.blit(msg_surface, msg_surface.get_rect(center=(width / 2, height * 0.95)))

    def start_new_game(self, mode):     # --- start_new_game() ---
                                        # แนะนำ: file_map.get(mode, 'words_medium.txt') ใช้ default parameter ได้แล้ว ดังนั้นไม่ต้องเช็คซ้ำ
        filename = {
                'classic': 'words_medium.txt',
                'unlimited': 'words_easy.txt',
                'limited_time': 'words_hard.txt'
            }.get(mode, 'words_medium.txt')
        
        self._load_words_from_file(filename)
        self.reset_game_state()
        self.current_mode = mode

        if not self.word_bank:
            print("Error: Word bank is empty. Cannot start game.")
            return False 
        
        self.target_word = random.choice(self.word_bank)
        
        if self.current_mode == 'limited_time':
            self.timer_start_time = pygame.time.get_ticks()
            
        print(f"Starting {mode} mode. Hint: {self.target_word}")
        return True

    def run_game(self): # --- run_game() ---
                        # แนะนำ: get_ui_rects() แค่คืนค่า gear_rect และ return_rect แล้วนำไปใช้ตรง event loop แทนที่จะคำนวณซ้ำทุก frame
        global SCREEN, WIDTH, HEIGHT
        running = True
        clock = pygame.time.Clock()
        
        def get_ui_rects():
            gear_size = int(min(WIDTH, HEIGHT) * 0.06)
            gear_rect = pygame.Rect(10, HEIGHT - gear_size - 10, gear_size, gear_size)
            return_rect = pygame.Rect(10, 10, gear_size, gear_size)
            return gear_rect, return_rect

        gear_rect_for_events, return_rect_for_events = get_ui_rects()

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                elif event.type == pygame.VIDEORESIZE:
                    WIDTH, HEIGHT = max(event.w, 500), max(event.h, 750) 
                    SCREEN = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
                    update_fonts(WIDTH, HEIGHT)

                    gear_rect_for_events, return_rect_for_events = get_ui_rects()
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if return_rect_for_events.collidepoint(event.pos) and not self.game_over:
                        running = False 
                        continue
                        
                    if gear_rect_for_events.collidepoint(event.pos) and not self.game_over:
                        settings_menu(self)
                        self.apply_volume_settings() 
                        continue
                    
                    if not self.game_over:
                        clicked_key = None
                        for key, rect in self.key_rects.items():
                            if rect.collidepoint(event.pos):
                                clicked_key = key
                                break
                        
                        if clicked_key:
                            if clicked_key == "ENTER":
                                if len(self.current_guess) == self.WORD_LENGTH:
                                    self.handle_enter()
                            elif clicked_key == "BACK":
                                self.current_guess = self.current_guess[:-1]
                            elif len(clicked_key) == 1 and len(self.current_guess) < self.WORD_LENGTH:
                                self.current_guess += clicked_key
                                self.play_sound("type")
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
                        self.play_sound("type")  

            if self.current_mode == 'limited_time' and not self.game_over:
                current_ticks = pygame.time.get_ticks()
                elapsed = current_ticks - self.timer_start_time
                self.time_remaining = (self.time_limit - elapsed) / 1000.0 

                if self.time_remaining <= 0:
                    self.time_remaining = 0
                    self.game_over = True
                    self.win = False 
                    self.set_message("TIME'S UP!", "RED")
                    
                    self._render_end_screen()
                    pygame.time.wait(250)
                    self._handle_end_game_sfx("lose")
                    self.update_stats() 

            if self.game_over:
                self._render_end_screen() 
            else:
                SCREEN.fill(BG_COLOR)
                self.draw_header(SCREEN)
                self.draw_board(SCREEN)
                self.draw_keyboard(SCREEN)
                self.draw_message(SCREEN)
                self.draw_settings_gear(SCREEN)
                self.draw_return_button(SCREEN) 
                
                pygame.display.flip()

            clock.tick(60)

def settings_menu(game):
    global SCREEN, WIDTH, HEIGHT

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
            changed = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.rect.collidepoint(event.pos) or self.knob.collidepoint(event.pos):
                    self.active = True
                    self.value = (event.pos[0] - self.rect.left) / self.rect.width
                    self.value = min(max(self.value, 0), 1) 
                    self.update_knob_position()
                    changed = True
            elif event.type == pygame.MOUSEBUTTONUP:
                self.active = False
            elif event.type == pygame.MOUSEMOTION and self.active:
                rel_x = min(max(event.pos[0], self.rect.left), self.rect.right)
                self.value = (rel_x - self.rect.left) / self.rect.width
                self.update_knob_position()
                changed = True
            return changed
        
        def draw(self, surface):
            pygame.draw.rect(surface, COLORS["LIGHT_GRAY"], self.rect, border_radius=5)
            pygame.draw.rect(surface, COLORS["WHITE"], self.knob, border_radius=5) 
    
    settings_running = True
    sound_enabled = bool(game.settings.get("sound_enabled", True))
    
    def create_ui(bg_val, fx_val):
        slider_width = WIDTH * 0.4
        slider_height = HEIGHT * 0.03
        bg_slider = VolumeSlider(WIDTH * 0.45, HEIGHT * 0.35, slider_width, slider_height, bg_val)
        fx_slider = VolumeSlider(WIDTH * 0.45, HEIGHT * 0.5, slider_width, slider_height, fx_val)
        sound_button = pygame.Rect(WIDTH * 0.3, HEIGHT * 0.2, WIDTH * 0.4, HEIGHT * 0.08)
        back_button = pygame.Rect(WIDTH * 0.3, HEIGHT * 0.8, WIDTH * 0.4, HEIGHT * 0.08)
        return bg_slider, fx_slider, sound_button, back_button

    bg_val = float(game.settings.get("bg_volume", DEFAULT_SETTINGS["bg_volume"]))
    fx_val = float(game.settings.get("fx_volume", DEFAULT_SETTINGS["fx_volume"]))
    bg_slider, fx_slider, sound_button, back_button = create_ui(bg_val, fx_val)

    def apply_and_save_settings():
        game.settings["bg_volume"] = bg_slider.value
        game.settings["fx_volume"] = fx_slider.value
        game.settings["sound_enabled"] = sound_enabled
        save_settings(game.settings)
        game.apply_volume_settings() 

    while settings_running:
        mx, my = pygame.mouse.get_pos()
        SCREEN.fill(BG_COLOR)
        
        draw_title(SCREEN, WIDTH, "Sound Settings", y=int(HEIGHT * 0.1))

        sound_text = "Sound: ON" if sound_enabled else "Sound: OFF"
        draw_button(SCREEN, sound_button, sound_text, mx, my, FONTS["stats"])

        bg_label = FONTS["stats"].render("Background Music", True, COLORS["WHITE"])
        fx_label = FONTS["stats"].render("Sound Effects", True, COLORS["WHITE"])
        SCREEN.blit(bg_label, (WIDTH * 0.12, HEIGHT * 0.34))
        SCREEN.blit(fx_label, (WIDTH * 0.12, HEIGHT * 0.49))
        bg_slider.draw(SCREEN)
        fx_slider.draw(SCREEN)

        draw_button(SCREEN, back_button, "Back", mx, my, FONTS["menu"])

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                apply_and_save_settings()
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.VIDEORESIZE:
                WIDTH, HEIGHT = max(event.w, 500), max(event.h, 750)
                SCREEN = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
                update_fonts(WIDTH, HEIGHT)
                bg_slider, fx_slider, sound_button, back_button = create_ui(bg_slider.value, fx_slider.value)
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if sound_button.collidepoint(event.pos):
                    sound_enabled = not sound_enabled
                    if sound_enabled:
                        try:
                            pygame.mixer.music.set_volume(bg_slider.value)
                            pygame.mixer.music.play(-1)
                        except Exception: pass
                    else:
                        try: pygame.mixer.music.stop()
                        except Exception: pass
                    apply_and_save_settings() 
                
                elif back_button.collidepoint(event.pos):
                    apply_and_save_settings()
                    settings_running = False

            bg_changed = bg_slider.handle_event(event)
            fx_changed = fx_slider.handle_event(event)
            if bg_changed or fx_changed:
                apply_and_save_settings()

        pygame.display.flip()

def display_stats(stats):
    global SCREEN, WIDTH, HEIGHT
    running = True

    def create_ui():
        return pygame.Rect(WIDTH * 0.3, HEIGHT * 0.82, WIDTH * 0.4, HEIGHT * 0.08)
    
    back_button = create_ui()

    while running:
        mx, my = pygame.mouse.get_pos()
        SCREEN.fill(BG_COLOR)

        draw_title(SCREEN, WIDTH, "Statistics", y=int(HEIGHT * 0.08))

        stats_text = [
            f"Played: {stats.get('played', 0)}",
            f"Wins: {stats.get('wins', 0)}",
            f"Current Streak: {stats.get('current_streak', 0)}",
            f"Max Streak: {stats.get('max_streak', 0)}"
        ]
        for i, text in enumerate(stats_text):
            surf = FONTS["stats"].render(text, True, COLORS["WHITE"])
            SCREEN.blit(surf, (WIDTH * 0.12, HEIGHT * (0.18 + i * 0.06)))

        dist_title = FONTS["stats"].render("Guess Distribution:", True, COLORS["WHITE"])
        SCREEN.blit(dist_title, (WIDTH * 0.12, HEIGHT * 0.44))
        guess_dist = stats.get("guess_dist", {})
        
        for i in range(1, 7): 
            count = guess_dist.get(str(i), 0)
            line = FONTS["message"].render(f"{i}: {count}", True, COLORS["WHITE"])
            SCREEN.blit(line, (WIDTH * 0.18, HEIGHT * (0.44 + 0.06 * i)))

        draw_button(SCREEN, back_button, "Back", mx, my, FONTS["menu"])

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.VIDEORESIZE:
                WIDTH, HEIGHT = max(event.w, 500), max(event.h, 750)
                SCREEN = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
                update_fonts(WIDTH, HEIGHT)
                back_button = create_ui() 
            if event.type == pygame.MOUSEBUTTONDOWN:
                if back_button.collidepoint(event.pos):
                    running = False 

        pygame.display.flip()

def mode_select_menu(game):
    global SCREEN, WIDTH, HEIGHT
    running = True
    button_texts = ["Classic", "Unlimited", "Limited Time", "Back"]
    
    while running:
        mx, my = pygame.mouse.get_pos()
        SCREEN.fill(BG_COLOR)

        draw_title(SCREEN, WIDTH, "Mode", y=int(HEIGHT * 0.15))
        buttons = draw_menu_buttons(SCREEN, mx, my, button_texts, 0.25, FONTS["stats"])
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
                if gear_rect.collidepoint(event.pos):
                    settings_menu(game)
                    game.apply_volume_settings()
                    continue

                for text, rect in buttons.items():
                    if rect.collidepoint(event.pos):
                        if text == "Classic":
                            if game.start_new_game('classic'): game.run_game()
                        elif text == "Unlimited":
                            if game.start_new_game('unlimited'): game.run_game()
                        elif text == "Limited Time":
                            if game.start_new_game('limited_time'): game.run_game()
                        elif text == "Back":
                            running = False 
        
        pygame.display.flip()

def main_menu():
    global SCREEN, WIDTH, HEIGHT
    game = WordleGamePygame() 
    button_texts = ["Play", "Statistics", "Exit"]
    
    while True:
        mx, my = pygame.mouse.get_pos()
        SCREEN.fill(BG_COLOR)
        
        draw_title(SCREEN, WIDTH, "Wordle", y=int(HEIGHT * 0.15))
        buttons = draw_menu_buttons(SCREEN, mx, my, button_texts, 0.25, FONTS["stats"])
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
                if gear_rect.collidepoint(event.pos):
                    settings_menu(game)
                    game.apply_volume_settings()
                    continue 
                
                for text, rect in buttons.items():
                    if rect.collidepoint(event.pos):
                        if text == 'Play':
                            mode_select_menu(game) 
                        elif text == 'Statistics':
                            display_stats(game.stats) 
                        elif text == 'Exit':
                            pygame.quit()
                            sys.exit()

        pygame.display.flip()

if __name__ == "__main__":
    main_menu()