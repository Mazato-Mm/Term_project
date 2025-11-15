import pygame
import random
import json
import os
import sys
from collections import Counter

pygame.init()
pygame.font.init()
pygame.mixer.init() 

# --- ค่าคงที่และการตั้งค่าเริ่มต้น ---
SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "settings.json")
DEFAULT_SETTINGS = {"sound_enabled": True, "bg_volume": 0.3, "fx_volume": 0.5}

WIDTH, HEIGHT = 600, 750
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Wordle BioHazard") 

# --- ฟังก์ชันสำหรับโหลดทรัพยากร (รูปภาพ, เสียง, ฟอนต์) ---

def load_image(filename, use_convert_alpha=True):
    """
    ฟังก์ชันสำหรับโหลดรูปภาพจากไฟล์ (เช่น icon, setting)
    พร้อมจัดการข้อผิดพลาดหากโหลดไม่สำเร็จ
    """
    path = os.path.join(os.path.dirname(__file__), filename)
    try:
        image = pygame.image.load(path)
        if use_convert_alpha:
            return image.convert_alpha()
        return image
    except Exception as e:
        print(f"Could not load image {filename}: {e}")
        return None

# โหลดไอคอนและรูปภาพ
try:
    icon = load_image("icon.png", use_convert_alpha=False)
    if icon:
        pygame.display.set_icon(icon)
except Exception as e:
    print(f"Could not set icon: {e}")

SETTING_IMG = load_image("setting_image.jpg")
RETURN_IMG = load_image("return_image.png")

# --- การตั้งค่าสี ---
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

# --- ฟังก์ชันจัดการไฟล์ Settings และ Fonts ---

def load_settings(path=SETTINGS_FILE):
    """
    โหลดการตั้งค่า (เสียง, ความดัง) จากไฟล์ JSON
    หากไฟล์ไม่พบหรือเสียหาย จะสร้างไฟล์ใหม่ด้วยค่าเริ่มต้น
    """
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
    save_settings(DEFAULT_SETTINGS, path) # สร้างไฟล์ใหม่ถ้าโหลดไม่สำเร็จ
    return DEFAULT_SETTINGS.copy()

def save_settings(settings, path=SETTINGS_FILE):
    """
    บันทึกการตั้งค่า (dict) ลงในไฟล์ JSON
    """
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Could not save settings: {e}")

def get_font(size):
    """
    โหลดฟอนต์ที่กำหนดเอง (ถ้ามีในโฟลเดอร์)
    หรือใช้ฟอนต์ระบบ (segoeui) หากไม่พบ
    """
    for f in ["Poppins-Regular.ttf", "Montserrat-Regular.ttf", "Kanit-Regular.ttf"]:
        if os.path.exists(f):
            return pygame.font.Font(f, size)
    return pygame.font.SysFont("segoeui", size, bold=True)

FONTS = {}
def update_fonts(width, height):
    """
    อัปเดตขนาดของฟอนต์ทั้งหมดตามขนาดหน้าจอปัจจุบัน
    เพื่อให้ UI ยังคงดูเหมาะสมเมื่อปรับขนาดหน้าจอ
    """
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
        # Fallback ในกรณีที่ get_font มีปัญหา
        for key, size in {"letter": 0.07, "menu": 0.06, "stats": 0.04, "message": 0.035, "key": 0.03, "end_game": 0.07, "button": 0.05}.items():
            FONTS[key] = pygame.font.Font(None, int(base_size * size))

update_fonts(WIDTH, HEIGHT) # โหลดฟอนต์ครั้งแรก

# --- ฟังก์ชันสำหรับวาด UI (ปุ่ม, หัวข้อ) ---

def draw_button(screen, rect, text, mx, my, font):
    """
    วาดปุ่มสไตล์ใหม่ (ขอบมน, มีเงา hover) ลงบนหน้าจอ
    """
    is_hover = rect.collidepoint((mx, my))
    color = BUTTON_HOVER if is_hover else BUTTON_COLOR
    pygame.draw.rect(screen, color, rect, border_radius=20)
    pygame.draw.rect(screen, TEXT_COLOR, rect, 3, border_radius=20) # วาดขอบ
    label = font.render(text, True, TEXT_COLOR)
    label_rect = label.get_rect(center=rect.center)
    screen.blit(label, label_rect)

def draw_title(screen, w, text, y=100):
    """
    วาดข้อความหัวเรื่องตรงกลางหน้าจอ
    """
    y_pos = int(HEIGHT * (y / 750)) 
    font_size = max(28, min(64, w // 14))
    title_font = get_font(font_size)
    label = title_font.render(text, True, TEXT_COLOR)
    label_rect = label.get_rect(center=(w // 2, y_pos))
    screen.blit(label, label_rect)

def draw_menu_buttons(screen, mx, my, button_texts, start_y_ratio, font):
    """
    ฟังก์ชันช่วยวาดปุ่มหลายๆ ปุ่มในแนวตั้งสำหรับเมนู
    คืนค่า dict ของปุ่มที่วาด (text: rect)
    """
    buttons = {}
    button_h, button_w = HEIGHT * 0.08, WIDTH * 0.7
    start_y = HEIGHT * start_y_ratio
    
    for i, text in enumerate(button_texts):
        y_pos = start_y + i * (button_h * 1.2)
        if text == "Back": # เพิ่มช่องว่างเล็กน้อยสำหรับปุ่ม Back
             y_pos += button_h * 0.3
             
        rect = pygame.Rect((WIDTH - button_w) / 2, y_pos, button_w, button_h)
        buttons[text] = rect
        draw_button(screen, rect, text, mx, my, font)
    return buttons

# --- คลาสหลักของเกม ---

class WordleGamePygame:
    """
    คลาสหลักที่จัดการตรรกะทั้งหมดของเกม Wordle
    รวมถึงสถานะเกม, การโหลดเสียง, การวาด, และการจัดการเหตุการณ์
    """
    
    def __init__(self, stats_file='wordle_stats_en.json'):
        """
        (Constructor) เริ่มต้นค่าตัวแปร, โหลดสถิติ, โหลดเสียง, และตั้งค่าเกมเริ่มต้น
        """
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

        # ตัวแปรสำหรับโหมดจับเวลา
        self.timer_start_time = 0
        self.time_limit = 30000 # 30 วินาที (ในหน่วยมิลลิวินาที)
        self.time_remaining = 30.0 # สำหรับแสดงผล

        # ฟังก์ชันย่อยสำหรับโหลดเสียง
        def load_sound(path):
            try:
                return pygame.mixer.Sound(path)
            except Exception as e:
                print(f"Could not load sound {path}: {e}")
                return None

        # โหลดเสียง SFX
        self.sounds = {
            "win": load_sound(os.path.join("sounds", "win.mp3")),
            "lose": load_sound(os.path.join("sounds", "lose.mp3")),
            "type": load_sound(os.path.join("sounds", "type.wav"))
        }
        
        # โหลดเสียง BGM
        try:
            pygame.mixer.music.load(os.path.join("sounds", "bg_music.mp3"))
        except Exception as e:
            print(f"Could not load bg music: {e}")

        # ใช้การตั้งค่าเสียง
        self.apply_volume_settings()
        
        if self.settings.get("sound_enabled", True):
            try:
                pygame.mixer.music.play(-1)
            except Exception: pass

    def apply_volume_settings(self):
        """
        ใช้การตั้งค่าความดังเสียง (จาก settings) กับเสียง BGM และ SFX
        """
        bg_vol = self.settings.get("bg_volume", DEFAULT_SETTINGS["bg_volume"])
        fx_vol = self.settings.get("fx_volume", DEFAULT_SETTINGS["fx_volume"])
        try:
            pygame.mixer.music.set_volume(bg_vol)
        except Exception: pass
        for sname in ("win", "lose", "type"):
            if self.sounds.get(sname):
                self.sounds[sname].set_volume(fx_vol)

    def play_sound(self, name):
        """
        เล่นเสียงเอฟเฟกต์ (เช่น ชนะ, แพ้, พิมพ์) ถ้าเสียงเปิดอยู่
        """
        if self.settings.get("sound_enabled", True) and name in self.sounds and self.sounds[name]:
            self.sounds[name].play()

    def reset_game_state(self):
        """
        รีเซ็ตสถานะเกม (การเดา, ผลลัพธ์, คีย์บอร์ด) เพื่อเริ่มเกมใหม่
        """
        self.guesses, self.results, self.current_guess = [], [], ""
        self.game_over, self.win = False, False
        self.message = ""
        self.keyboard_colors = {chr(c): "KEY_DEFAULT" for c in range(ord('a'), ord('z') + 1)}
        self.key_rects = {} 
        # รีเซ็ตตัวจับเวลา
        self.timer_start_time = 0
        self.time_remaining = 30.0

    def set_message(self, text, color_name="WHITE"):
        """
        ตั้งค่าข้อความแจ้งเตือน (เช่น "คำไม่ถูกต้อง") ให้แสดงชั่วคราว
        """
        if isinstance(color_name, str):
            color = COLORS.get(color_name, COLORS["WHITE"])
        else:
            color = color_name
        self.message = (text, color)
        self.message_timer = pygame.time.get_ticks()

    def _load_words_from_file(self, filename):
        """
        โหลดรายการคำศัพท์จากไฟล์ .txt สำหรับโหมดเกมที่เลือก
        """
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
        """
        โหลดสถิติการเล่น (เล่น, ชนะ, ฯลฯ) จากไฟล์ JSON
        """
        if not os.path.exists(self.stats_file):
            return {"played": 0, "wins": 0, "current_streak": 0, "max_streak": 0, "guess_dist": {}}
        try:
            with open(self.stats_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {"played": 0, "wins": 0, "current_streak": 0, "max_streak": 0, "guess_dist": {}}

    def _save_stats(self):
        """
        บันทึกสถิติการเล่นปัจจุบันลงไฟล์ JSON
        """
        try:
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Could not save stats: {e}")

    def update_stats(self):
        """
        อัปเดตสถิติหลังจบเกม (เพิ่มการเล่น, ชนะ/แพ้, streak)
        """
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
        """
        ตรวจสอบคำเดาเทียบกับคำตอบ และคืนผลลัพธ์ (เขียว, เหลือง, เทา)
        """
        result = ["GRAY"] * self.WORD_LENGTH
        target_counts = Counter(self.target_word)
        
        # ตรวจสอบตัวที่ถูก (สีเขียว) ก่อน
        for i, letter in enumerate(guess):
            if letter == self.target_word[i]:
                result[i] = "GREEN"
                target_counts[letter] -= 1
        
        # ตรวจสอบตัวที่เกือบถูก (สีเหลือง)
        for i, letter in enumerate(guess):
            if result[i] != "GREEN" and letter in target_counts and target_counts[letter] > 0:
                result[i] = "YELLOW"
                target_counts[letter] -= 1
        
        # อัปเดตสีคีย์บอร์ด
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
        """
        ตรวจสอบว่าคำเดาถูกต้องตามรูปแบบหรือไม่ (เช่น ความยาว)
        """
        if len(guess) != self.WORD_LENGTH:
            self.set_message(f"Guess must be {self.WORD_LENGTH} letters", "RED")
            return False
        # (สามารถเพิ่มการตรวจสอบว่าคำมีใน word bank หรือไม่ ที่นี่)
        return True

    def _render_end_screen(self):
        """
        วาดหน้าจอเมื่อจบเกม (แสดงข้อความ ชนะ/แพ้ และคำตอบ)
        (แก้ไข) จะวาดทับพื้นหลังสีทึบ และไม่แสดงไอคอน
        """
        try:
            # 🌟 (แก้ไข) เติมสีพื้นหลังทึบ (ไม่วาดบอร์ดหรือคีย์บอร์ด)
            SCREEN.fill(BG_COLOR) 
            
            end_text_str, color = self.message
            
            # 🌟 (เพิ่ม) ตรวจสอบโหมด Unlimited เพื่อเพิ่มข้อความ
            if self.win and self.current_mode == 'unlimited':
                guess_count = len(self.guesses)
                end_text_str = f"YOU WIN! ({guess_count} guesses)"
            
            # แสดงข้อความผลลัพธ์ (ชนะ/แพ้/หมดเวลา)
            end_text_surf = FONTS["end_game"].render(end_text_str, True, color)
            SCREEN.blit(end_text_surf, end_text_surf.get_rect(center=(WIDTH / 2, HEIGHT / 2 - 30)))
            
            # แสดงคำตอบถ้าแพ้
            if not self.win:
                answer_surf = FONTS["message"].render(f"The word was: {self.target_word.upper()}", True, COLORS["WHITE"])
                SCREEN.blit(answer_surf, answer_surf.get_rect(center=(WIDTH / 2, HEIGHT / 2 + 15)))
                
            # แสดงข้อความให้กลับเมนู
            prompt_surf = FONTS["message"].render("Press Enter to return to menu", True, COLORS["WHITE"])
            SCREEN.blit(prompt_surf, prompt_surf.get_rect(center=(WIDTH / 2, HEIGHT - 50)))
            
            # 🌟 (แก้ไข) ลบการวาด self.draw_settings_gear(SCREEN)
            # 🌟 (แก้ไข) ลบการวาด self.draw_return_button(SCREEN) 
            
            pygame.display.flip() # 🌟 (สำคัญ) flip ภายในฟังก์ชันนี้
        except Exception as e:
            print(f"Error rendering end screen: {e}")

    def _handle_end_game_sfx(self, sound_name):
        """
        จัดการการเล่นเสียงเมื่อจบเกม (หยุด BGM ชั่วคราว, เล่นเสียง ชนะ/แพ้)
        """
        try:
            bg_pos = pygame.mixer.music.get_pos() # จำตำแหน่ง BGM
            pygame.mixer.music.stop()
        except Exception:
            bg_pos = None
            
        # เล่นเสียง ชนะ/แพ้
        if self.settings.get("sound_enabled", True) and self.sounds.get(sound_name):
            self.sounds[sound_name].play()
            pygame.time.wait(int(self.sounds[sound_name].get_length() * 1000))
        
        # กลับมาเล่น BGM ต่อ (ถ้าเปิดเสียงอยู่)
        if self.settings.get("sound_enabled", True):
            try:
                if bg_pos is not None and bg_pos >= 0: 
                    pygame.mixer.music.play(-1, bg_pos / 1000.0) # เล่นต่อจากจุดเดิม
                else:
                    pygame.mixer.music.play(-1)
            except Exception:
                try:
                    pygame.mixer.music.play(-1) # พยายามเล่นใหม่
                except Exception:
                    pass 

    def handle_enter(self):
        """
        ประมวลผลเมื่อผู้เล่นกด Enter (ตรวจสอบคำเดา, อัปเดตบอร์ด, ตรวจสอบ ชนะ/แพ้)
        """
        if self.game_over: # ถ้าเกมจบทแล้ว (เช่น หมดเวลา) ไม่ต้องทำอะไร
            return
        
        if self.is_valid_guess(self.current_guess):
            self.guesses.append(self.current_guess)
            self.results.append(self.check_guess(self.current_guess))
            self.current_guess = ""
            
            # ตรวจสอบว่าชนะหรือไม่
            if self.guesses[-1] == self.target_word:
                self.win = self.game_over = True
                self.set_message("YOU WIN", "GREEN")
                
                self._render_end_screen() 
                pygame.time.wait(250)     
                self._handle_end_game_sfx("win") 
                
                if self.current_mode != 'unlimited':
                    self.update_stats()

            # ตรวจสอบว่าแพ้ (เดาครบ 6 ครั้ง) หรือไม่
            elif len(self.guesses) == self.MAX_GUESSES and self.current_mode != 'unlimited':
                self.game_over = True
                self.set_message("LOSE", "RED")
                
                self._render_end_screen() 
                pygame.time.wait(250)     
                self._handle_end_game_sfx("lose") 
                
                if self.current_mode != 'unlimited':
                    self.update_stats()

    def draw_board(self, surface):
        """
        วาดตาราง Wordle (กล่องตัวอักษร) ลงบนหน้าจอ
        รองรับโหมด Unlimited (แสดงเฉพาะ 5 แถวสุดท้าย + แถวปัจจุบัน)
        """
        width, height = surface.get_size()
        
        # --- คำนวณขนาดและตำแหน่งของตาราง ---
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
        # --- จบการคำนวณ ---

        # กรณีโหมด Unlimited: แสดงผลต่างออกไป
        if self.current_mode == 'unlimited' and not self.game_over:
            guesses_to_show = self.guesses[-1:-6:-1] # 5 แถวสุดท้าย (ย้อนกลับ)
            results_to_show = self.results[-1:-6:-1]
            num_history_rows_to_show = min(len(self.guesses), 5)
            total_rows_to_draw = 1 + num_history_rows_to_show # 1 (แถวปัจจุบัน) + ประวัติ

            for i in range(total_rows_to_draw): 
                y_pos = start_y + i * (box_size + padding)
                
                if i == 0: # วาดแถวปัจจุบัน (แถวบนสุด)
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
                            
                else: # วาดแถวประวัติ (5 แถวล่าสุด)
                    guess_idx = i - 1 
                    guess = guesses_to_show[guess_idx]
                    result = results_to_show[guess_idx]
                    
                    for j in range(self.WORD_LENGTH):
                        box = pygame.Rect(start_x + j * (box_size + padding), y_pos, box_size, box_size)
                        letter, color_key, l_color = guess[j], result[j], COLORS["WHITE"]
                        pygame.draw.rect(surface, COLORS[color_key], box, border_radius=5)
                        
                        text_surf = FONTS["letter"].render(letter.upper(), True, l_color)
                        surface.blit(text_surf, text_surf.get_rect(center=box.center))
            return # จบการวาดสำหรับโหมด Unlimited

        # กรณีโหมด Classic/Hard (วาดปกติ 6 แถว)
        for i in range(self.MAX_GUESSES): 
            for j in range(self.WORD_LENGTH):
                box = pygame.Rect(start_x + j * (box_size + padding), start_y + i * (box_size + padding), box_size, box_size)
                letter, color_key, l_color = "", "BLACK", COLORS["WHITE"] 
                
                if i < len(self.guesses): # แถวที่เดาไปแล้ว
                    letter, color_key, l_color = self.guesses[i][j], self.results[i][j], COLORS["WHITE"]
                    pygame.draw.rect(surface, COLORS[color_key], box, border_radius=5)
                elif i == len(self.guesses) and j < len(self.current_guess) and not self.game_over: # แถวที่กำลังพิมพ์
                    letter = self.current_guess[j]
                    pygame.draw.rect(surface, COLORS["BLACK"], box, border_radius=5) 
                    pygame.draw.rect(surface, COLORS["GRAY"], box, 2, border_radius=5) 
                    l_color = COLORS["WHITE"] 
                else: # แถวว่าง
                    pygame.draw.rect(surface, COLORS["BLACK"], box, border_radius=5) 
                    pygame.draw.rect(surface, COLORS["GRAY"], box, 2, border_radius=5) 

                if letter:
                    text_surf = FONTS["letter"].render(letter.upper(), True, l_color)
                    surface.blit(text_surf, text_surf.get_rect(center=box.center))

    def draw_keyboard(self, surface):
        """
        วาดแป้นพิมพ์เสมือนจริง (QWERTY) พร้อมสีที่อัปเดตแล้ว
        เก็บตำแหน่ง (Rect) ของแต่ละปุ่มไว้ใน self.key_rects
        """
        self.key_rects.clear() 
        width, height = surface.get_size()
        
        key_rows = [
            list("qwertyuiop"), 
            list("asdfghjkl"), 
            ["ENTER"] + list("zxcvbnm") + ["BACK"]
        ]
        
        # คำนวณขนาดและตำแหน่ง
        keyboard_area_y = height * 0.25 
        key_h = (keyboard_area_y / 4) * 0.9 
        key_w = min(width * 0.08, key_h * 1.3) 
        padding = key_w * 0.15
        start_y = height * 0.7 

        for i, row in enumerate(key_rows):
            # คำนวณความกว้างแถว (ปุ่ม ENTER/BACK กว้างกว่า)
            total_key_units = 0
            for key in row:
                total_key_units += 1 if len(key) == 1 else 1.5 
            
            row_width = (total_key_units * key_w) + ((len(row) - 1) * padding)
            current_x = (width - row_width) / 2
            current_y = start_y + i * (key_h + padding * 0.8)

            # วาดแต่ละปุ่มในแถว
            for key in row:
                current_key_w = key_w
                color_name = self.keyboard_colors.get(key, "KEY_DEFAULT") 
                
                if key == "ENTER" or key == "BACK":
                    current_key_w = key_w * 1.5
                    color_name = "KEY_DEFAULT"
                
                key_rect = pygame.Rect(current_x, current_y, current_key_w, key_h)
                self.key_rects[key] = key_rect # เก็บ Rect สำหรับการคลิก
                
                pygame.draw.rect(surface, COLORS[color_name], key_rect, border_radius=8)
                
                key_text_str = key.upper()
                if key == "BACK":
                    key_text_str = "<=" 
                
                key_text = FONTS["key"].render(key_text_str, True, COLORS["WHITE"])
                surface.blit(key_text, key_text.get_rect(center=key_rect.center))
                
                current_x += current_key_w + padding

    def draw_header(self, surface):
        """
        วาดหัวข้อด้านบน (ชื่อโหมด และ ตัวจับเวลา)
        """
        width, height = surface.get_size()
        
        # 🌟 (เปลี่ยนชื่อ) อัปเกรด .capitalize()
        # เพื่อให้ 'limited_time' แสดงเป็น 'Limited Time'
        mode_text = f"Mode: {self.current_mode.replace('_', ' ').title()}"
        
        title_text = FONTS["menu"].render(mode_text, True, COLORS["WHITE"])
        surface.blit(title_text, title_text.get_rect(center=(width / 2, height * 0.04)))

        # 🌟 (เปลี่ยนชื่อ) แสดงตัวจับเวลาในโหมด Limited Time
        if self.current_mode == 'limited_time' and not self.game_over:
            # ปัดเศษขึ้นเพื่อให้แสดง 30 ตอนเริ่ม และ 1 วินาทีสุดท้าย
            timer_display = max(0, int(self.time_remaining + 0.99)) 
            timer_text = f"Time: {timer_display}"
            # เปลี่ยนเป็นสีแดงเมื่อเหลือน้อย
            timer_color = COLORS["WHITE"] if self.time_remaining > 5 else COLORS["RED"]
            timer_surf = FONTS["stats"].render(timer_text, True, timer_color)
            timer_rect = timer_surf.get_rect(topright=(width - 20, height * 0.02))
            surface.blit(timer_surf, timer_rect)

    def draw_settings_gear(self, surface):
        """
        วาดไอคอนรูปเฟือง (หรือข้อความ "⚙") สำหรับปุ่มตั้งค่า
        """
        width, height = surface.get_size()
        margin = 10
        gear_size = int(min(width, height) * 0.06)
        gear_rect = pygame.Rect(margin, height - gear_size - margin, gear_size, gear_size) 

        try:
            if not SETTING_IMG: raise ValueError("No setting image")
            img = pygame.transform.smoothscale(SETTING_IMG, (gear_size, gear_size))
            surface.blit(img, gear_rect)
        except Exception:
            # Fallback ถ้าไม่มีรูป
            gear_surf = FONTS["menu"].render("⚙", True, COLORS["WHITE"])
            surface.blit(gear_surf, gear_surf.get_rect(center=gear_rect.center))
        return gear_rect 
    
    def draw_return_button(self, surface):
        """
        วาดไอคอนลูกศร (หรือข้อความ "<-") สำหรับปุ่มย้อนกลับ
        """
        width, height = surface.get_size()
        margin = 10
        btn_size = int(min(width, height) * 0.06) 
        btn_rect = pygame.Rect(margin, margin, btn_size, btn_size) 

        try:
            if not RETURN_IMG: raise ValueError("No return image")
            img = pygame.transform.smoothscale(RETURN_IMG, (btn_size, btn_size))
            surface.blit(img, btn_rect)
        except Exception:
            # Fallback ถ้าไม่มีรูป
            fallback_text = FONTS["menu"].render("<-", True, COLORS["WHITE"])
            surface.blit(fallback_text, fallback_text.get_rect(center=btn_rect.center))
        return btn_rect
    
    def draw_message(self, surface):
        """
        วาดข้อความแจ้งเตือนชั่วคราว (จาก set_message)
        """
        width, height = surface.get_size()
        if self.message and pygame.time.get_ticks() - self.message_timer < 2000 and not self.game_over:
            text, color = self.message
            msg_surface = FONTS["message"].render(text, True, color)
            surface.blit(msg_surface, msg_surface.get_rect(center=(width / 2, height * 0.95)))

    def start_new_game(self, mode):
        """
        เริ่มต้นเกมใหม่ในโหมดที่เลือก (โหลดคำ, รีเซ็ตสถานะ, เริ่มจับเวลา)
        """
        # 🌟 (เปลี่ยนชื่อ) อัปเดต key สำหรับไฟล์คำศัพท์
        file_map = {'classic': 'words_medium.txt', 'unlimited': 'words_easy.txt', 'limited_time': 'words_hard.txt'}
        filename = file_map.get(mode, 'words_medium.txt')
        
        self._load_words_from_file(filename)
        self.reset_game_state()
        self.current_mode = mode
        if not self.word_bank:
            print("Error: Word bank is empty. Cannot start game.")
            return False 
        self.target_word = random.choice(self.word_bank)
        
        # 🌟 (เปลี่ยนชื่อ) เริ่มจับเวลาถ้าเป็นโหมด Limited Time
        if self.current_mode == 'limited_time':
            self.timer_start_time = pygame.time.get_ticks()
            
        print(f"Starting {mode} mode. Hint: {self.target_word}")
        return True

    def run_game(self):
        """
        ลูปหลักของเกม (Game Loop) สำหรับหน้าเล่นเกม
        จัดการ input, อัปเดตตรรกะ, และวาดหน้าจอ
        """
        global SCREEN, WIDTH, HEIGHT
        running = True
        clock = pygame.time.Clock()
        
        # ฟังก์ชันย่อยสำหรับดึงตำแหน่งปุ่ม UI (เฟือง, ย้อนกลับ)
        def get_ui_rects():
            gear_margin = 10
            gear_size = int(min(WIDTH, HEIGHT) * 0.06)
            gear_rect = pygame.Rect(gear_margin, HEIGHT - gear_size - gear_margin, gear_size, gear_size)
            
            return_margin = 10
            return_size = int(min(WIDTH, HEIGHT) * 0.06)
            return_rect = pygame.Rect(return_margin, return_margin, return_size, return_size)
            return gear_rect, return_rect

        gear_rect_for_events, return_rect_for_events = get_ui_rects()

        while running:
            # --- 1. จัดการ Event (Input) ---
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                # ปรับขนาดหน้าจอ
                if event.type == pygame.VIDEORESIZE:
                    WIDTH, HEIGHT = max(event.w, 500), max(event.h, 750) 
                    SCREEN = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
                    update_fonts(WIDTH, HEIGHT) 
                    gear_rect_for_events, return_rect_for_events = get_ui_rects()
                
                # คลิกเมาส์
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if return_rect_for_events.collidepoint(event.pos) and not self.game_over:
                        running = False # กลับไปหน้าเลือกโหมด
                        continue
                        
                    if gear_rect_for_events.collidepoint(event.pos) and not self.game_over:
                        settings_menu(self)
                        self.apply_volume_settings() # ใช้การตั้งค่าใหม่
                        continue
                    
                    if not self.game_over:
                        # ตรวจสอบการคลิกคีย์บอร์ด
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

                # กดคีย์บอร์ด
                if event.type == pygame.KEYDOWN:
                    if self.game_over:
                        if event.key in [pygame.K_RETURN, pygame.K_ESCAPE]:
                            running = False # กลับเมนูหลังจบเกม
                        continue
                    
                    if event.key == pygame.K_ESCAPE:
                        running = False # ออกจากเกม
                    elif event.key == pygame.K_BACKSPACE:
                        self.current_guess = self.current_guess[:-1]
                    elif event.key == pygame.K_RETURN and len(self.current_guess) == self.WORD_LENGTH:
                        self.handle_enter()
                    elif 'a' <= event.unicode.lower() <= 'z' and len(self.current_guess) < self.WORD_LENGTH:
                        self.current_guess += event.unicode.lower()
                        self.play_sound("type")  

            # --- 2. อัปเดตตรรกะ (Update Logic) ---
            
            # 🌟 (เปลี่ยนชื่อ) ตรรกะการจับเวลาสำหรับโหมด Limited Time
            if self.current_mode == 'limited_time' and not self.game_over:
                current_ticks = pygame.time.get_ticks()
                elapsed = current_ticks - self.timer_start_time
                self.time_remaining = (self.time_limit - elapsed) / 1000.0 # แปลงเป็นวินาที (ทศนิยม)

                if self.time_remaining <= 0:
                    self.time_remaining = 0
                    self.game_over = True
                    self.win = False # แพ้เพราะหมดเวลา
                    self.set_message("TIME'S UP!", "RED")
                    
                    # เรียกกระบวนการจบเกม (เสียง, สถิติ)
                    self._render_end_screen()
                    pygame.time.wait(250)
                    self._handle_end_game_sfx("lose")
                    self.update_stats() # บันทึกสถิติว่าแพ้
            # --- จบส่วนจับเวลา ---


            # --- 3. วาดหน้าจอ (Draw) ---
            if self.game_over:
                # ถ้าเกมจบ, วาดหน้าจอจบเกม (ซึ่งจะ fill BG และ flip เอง)
                self._render_end_screen() 
            else:
                # ถ้าเกมยังไม่จบ, วาดหน้าจอเกมปกติ
                SCREEN.fill(BG_COLOR)
                self.draw_header(SCREEN)
                self.draw_board(SCREEN)
                self.draw_keyboard(SCREEN)
                self.draw_message(SCREEN)
                self.draw_settings_gear(SCREEN)
                self.draw_return_button(SCREEN) 
                
                # Flip display สำหรับหน้าจอเกม
                pygame.display.flip()

            clock.tick(60)

# --- ฟังก์ชันสำหรับหน้าจอเมนูต่างๆ ---

def settings_menu(game):
    """
    หน้าจอสำหรับจัดการการตั้งค่า (เปิด/ปิดเสียง, ปรับความดัง)
    """
    global SCREEN, WIDTH, HEIGHT

    class VolumeSlider:
        """
        (คลาสย่อย) คลาสสำหรับวาดและจัดการแถบเลื่อนปรับความดัง
        """
        def __init__(self, x, y, width, height, initial_value=0.5):
            self.rect = pygame.Rect(x, y, width, height)
            self.knob = pygame.Rect(x, y, 20, height)
            self.value = initial_value
            self.active = False
            self.update_knob_position()
        
        def update_knob_position(self):
            # อัปเดตตำแหน่งปุ่มจับตามค่า value (0.0 - 1.0)
            self.knob.centerx = self.rect.left + (self.rect.width * self.value)
            self.knob.centery = self.rect.centery
        
        def handle_event(self, event):
            # จัดการการลากแถบเลื่อน
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
            # วาดแถบและปุ่มจับ
            pygame.draw.rect(surface, COLORS["LIGHT_GRAY"], self.rect, border_radius=5)
            pygame.draw.rect(surface, COLORS["WHITE"], self.knob, border_radius=5) 
    
    # --- เริ่มต้นเมนูตั้งค่า ---
    settings_running = True
    sound_enabled = bool(game.settings.get("sound_enabled", True))
    
    # ฟังก์ชันสร้าง UI (เผื่อปรับขนาดจอ)
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

    # ฟังก์ชันบันทึกและใช้ค่า
    def apply_and_save_settings():
        game.settings["bg_volume"] = bg_slider.value
        game.settings["fx_volume"] = fx_slider.value
        game.settings["sound_enabled"] = sound_enabled
        save_settings(game.settings)
        game.apply_volume_settings() # ใช้ค่าทันที

    # ลูปของหน้าตั้งค่า
    while settings_running:
        mx, my = pygame.mouse.get_pos()
        SCREEN.fill(BG_COLOR)
        
        draw_title(SCREEN, WIDTH, "Sound Settings", y=int(HEIGHT * 0.1))

        # วาดปุ่มเปิด/ปิดเสียง
        sound_text = "Sound: ON" if sound_enabled else "Sound: OFF"
        draw_button(SCREEN, sound_button, sound_text, mx, my, FONTS["stats"])

        # วาดแถบเลื่อน
        bg_label = FONTS["stats"].render("Background Music", True, COLORS["WHITE"])
        fx_label = FONTS["stats"].render("Sound Effects", True, COLORS["WHITE"])
        SCREEN.blit(bg_label, (WIDTH * 0.12, HEIGHT * 0.34))
        SCREEN.blit(fx_label, (WIDTH * 0.12, HEIGHT * 0.49))
        bg_slider.draw(SCREEN)
        fx_slider.draw(SCREEN)

        # วาดปุ่มย้อนกลับ
        draw_button(SCREEN, back_button, "Back", mx, my, FONTS["menu"])

        # จัดการ Event
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
                    # เปิด/ปิดเสียง
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
                    # กลับ
                    apply_and_save_settings()
                    settings_running = False

            # จัดการการลากแถบเลื่อน
            bg_changed = bg_slider.handle_event(event)
            fx_changed = fx_slider.handle_event(event)
            if bg_changed or fx_changed:
                apply_and_save_settings()

        pygame.display.flip()

def display_stats(stats):
    """
    หน้าจอสำหรับแสดงสถิติการเล่น
    """
    global SCREEN, WIDTH, HEIGHT
    running = True

    def create_ui():
        # สร้างปุ่ม Back
        return pygame.Rect(WIDTH * 0.3, HEIGHT * 0.82, WIDTH * 0.4, HEIGHT * 0.08)
    
    back_button = create_ui()

    while running:
        mx, my = pygame.mouse.get_pos()
        SCREEN.fill(BG_COLOR)

        draw_title(SCREEN, WIDTH, "Statistics", y=int(HEIGHT * 0.08))

        # แสดงสถิติหลัก
        stats_text = [
            f"Played: {stats.get('played', 0)}",
            f"Wins: {stats.get('wins', 0)}",
            f"Current Streak: {stats.get('current_streak', 0)}",
            f"Max Streak: {stats.get('max_streak', 0)}"
        ]
        for i, text in enumerate(stats_text):
            surf = FONTS["stats"].render(text, True, COLORS["WHITE"])
            SCREEN.blit(surf, (WIDTH * 0.12, HEIGHT * (0.18 + i * 0.06)))

        # แสดงสถิติการเดา
        dist_title = FONTS["stats"].render("Guess Distribution:", True, COLORS["WHITE"])
        SCREEN.blit(dist_title, (WIDTH * 0.12, HEIGHT * 0.44))
        guess_dist = stats.get("guess_dist", {})
        
        for i in range(1, 7): 
            count = guess_dist.get(str(i), 0)
            line = FONTS["message"].render(f"{i}: {count}", True, COLORS["WHITE"])
            SCREEN.blit(line, (WIDTH * 0.18, HEIGHT * (0.44 + 0.06 * i)))

        # วาดปุ่ม Back
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
                    running = False # กลับเมนูหลัก

        pygame.display.flip()

def mode_select_menu(game):
    """
    หน้าจอสำหรับเลือกโหมดเกม (Classic, Unlimited, Limited Time)
    """
    global SCREEN, WIDTH, HEIGHT
    running = True
    # 🌟 (เปลี่ยนชื่อ) อัปเดตข้อความบนปุ่ม
    button_texts = ["Classic", "Unlimited", "Limited Time", "Back"]
    
    while running:
        mx, my = pygame.mouse.get_pos()
        SCREEN.fill(BG_COLOR)

        draw_title(SCREEN, WIDTH, "Mode", y=int(HEIGHT * 0.15))
        # ใช้ฟังก์ชันช่วยวาดปุ่ม
        buttons = draw_menu_buttons(SCREEN, mx, my, button_texts, 0.25, FONTS["stats"])
        gear_rect = game.draw_settings_gear(SCREEN) # วาดปุ่มตั้งค่า

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

                # ตรวจสอบการคลิกปุ่มโหมด
                for text, rect in buttons.items():
                    if rect.collidepoint(event.pos):
                        if text == "Classic":
                            if game.start_new_game('classic'): game.run_game()
                        elif text == "Unlimited":
                            if game.start_new_game('unlimited'): game.run_game()
                        # 🌟 (เปลี่ยนชื่อ) อัปเดตเงื่อนไขการคลิก
                        elif text == "Limited Time":
                            # 🌟 (เปลี่ยนชื่อ) อัปเดต ID ที่ส่งไป
                            if game.start_new_game('limited_time'): game.run_game()
                        elif text == "Back":
                            running = False # กลับเมนูหลัก
        
        pygame.display.flip()

def main_menu():
    """
    หน้าจอเมนูหลัก (Play, Statistics, Exit)
    นี่คือลูปหลักของโปรแกรม
    """
    global SCREEN, WIDTH, HEIGHT
    game = WordleGamePygame() # สร้าง instance ของเกม
    button_texts = ["Play", "Statistics", "Exit"]
    
    while True:
        mx, my = pygame.mouse.get_pos()
        SCREEN.fill(BG_COLOR)
        
        draw_title(SCREEN, WIDTH, "Wordle", y=int(HEIGHT * 0.15))
        # ใช้ฟังก์ชันช่วยวาดปุ่ม
        buttons = draw_menu_buttons(SCREEN, mx, my, button_texts, 0.25, FONTS["stats"])
        gear_rect = game.draw_settings_gear(SCREEN) # วาดปุ่มตั้งค่า

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
                
                # ตรวจสอบการคลิกปุ่มเมนูหลัก
                for text, rect in buttons.items():
                    if rect.collidepoint(event.pos):
                        if text == 'Play':
                            mode_select_menu(game) # ไปหน้าเลือกโหมด
                        elif text == 'Statistics':
                            display_stats(game.stats) # ไปหน้าสถิติ
                        elif text == 'Exit':
                            pygame.quit()
                            sys.exit()

        pygame.display.flip()

if __name__ == "__main__":
    """
    จุดเริ่มต้นของโปรแกรม: เรียก main_menu()
    """
    main_menu()
