import tkinter as tk
from stockfish import Stockfish
import mss
import cv2
import numpy as np
import keyboard
import threading
import time
import chess
import pyautogui
import random

# Начальная безопасная пауза для pyautogui
pyautogui.PAUSE = 0.05

# 1. Путь к твоему движку Stockfish
STOCKFISH_PATH = r"C:\Users\mi-li\Desktop\stockfish\stockfish-windows-x86-64-sse41-popcnt.exe"

try:
    # МАКСИМАЛЬНЫЙ ИНТЕЛЛЕКТ (глубина 18), но с оптимизированным хэшем (512 МБ) и 2 потоками,
    # чтобы меню не зависало при старте и запускалось мгновенно.
    engine = Stockfish(path=STOCKFISH_PATH, depth=18)
    engine.update_engine_parameters({
        "Threads": 2, 
        "Hash": 512,
        "Skill Level": 20
    })
except Exception as e:
    engine = None

board = chess.Board()
my_color = "white"  
auto_mode = False   
last_processed_move = None  
is_minimized = False  

# Значения задержки по умолчанию для рандомайзера
delay_min = 0.1  
delay_max = 0.3  

# Вшитые координаты твоей доски
board_left = 400
board_top = 147
board_right = 995
board_bottom = 737
square_size = 74.375

PIECE_NAMES = {
    chess.PAWN: "Пешка",
    chess.KNIGHT: "Конь",
    chess.BISHOP: "Слон",
    chess.ROOK: "Ладья",
    chess.QUEEN: "Ферзь",
    chess.KING: "Король"
}

root = tk.Tk()
root.title("Lichess Helper")
root.attributes("-topmost", True)
root.configure(bg='#1A1A1A')  
root.attributes('-alpha', 0.96)
root.overrideredirect(True)  

WINDOW_WIDTH = 340
WINDOW_HEIGHT = 275  
MINI_SIZE = 45  

screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{int(screen_width/2 - WINDOW_WIDTH/2)}+{int(screen_height/2 - WINDOW_HEIGHT/2)}")

top_bar = tk.Frame(root, bg='#262626', height=30)
top_bar.pack(fill='x', side='top')

title_label = tk.Label(top_bar, text="🤖 STOCKFISH SMART MODE", font=("Segoe UI", 9, "bold"), fg="#81C784", bg="#262626")
title_label.pack(side='left', padx=10, pady=5)

main_container = tk.Frame(root, bg='#1A1A1A')
main_container.pack(fill='both', expand=True, padx=15, pady=5)

label = tk.Label(
    main_container, text="F4 - Ход | F3 - Авто-игра | F2 - Сброс\nF9 - Исправить рассинхрон", 
    font=("Segoe UI", 10, "bold"), fg="#81C784", bg="#1A1A1A", justify="center"
)
label.pack(pady=5)

btn_frame = tk.Frame(main_container, bg='#1A1A1A')
btn_frame.pack(pady=2)

def update_color_button_ui():
    global my_color
    if my_color == "white":
        color_btn.config(text="ЦВЕТ: БЕЛЫЕ", bg="#2E7D32", fg="#E8F5E9")
    else:
        color_btn.config(text="ЦВЕТ: ЧЕРНЫЕ", bg="#424242", fg="#FFFFFF")

def toggle_color():
    global my_color
    if my_color == "white":
        my_color = "black"
    else:
        my_color = "white"
    update_color_button_ui()

color_btn = tk.Button(
    btn_frame, text="ЦВЕТ: БЕЛЫЕ", command=toggle_color,
    bg="#2E7D32", fg="#E8F5E9", bd=0, font=("Segoe UI", 9, "bold"), height=1, width=15,
    activebackground="#388E3C", activeforeground="#FFFFFF", cursor="hand2"
)
color_btn.pack(side='left', padx=4)
update_color_button_ui()

def toggle_auto_mode():
    global auto_mode
    if not auto_mode:
        auto_mode = True
        auto_btn.config(text="АВТО: ВКЛ", bg="#C62828", fg="#FFEBEE")
        threading.Thread(target=auto_play_loop, daemon=True).start()
    else:
        auto_mode = False
        auto_btn.config(text="АВТО: ВЫКЛ", bg="#37474F", fg="#ECEFF1")

auto_btn = tk.Button(
    btn_frame, text="АВТО: ВЫКЛ", command=toggle_auto_mode,
    bg="#37474F", fg="#ECEFF1", bd=0, font=("Segoe UI", 9, "bold"), height=1, width=15,
    activebackground="#455A64", activeforeground="#FFFFFF", cursor="hand2"
)
auto_btn.pack(side='left', padx=4)

# --- БЛОК НАСТРОЙКИ ЗАДЕРЖЕК ---
delay_frame = tk.Frame(main_container, bg='#212121', bd=1, relief='solid')
delay_frame.pack(fill='x', pady=8, padx=5)

lbl_from = tk.Label(delay_frame, text="От:", font=("Segoe UI", 9, "bold"), fg="#B0BEC5", bg="#212121")
lbl_from.pack(side='left', padx=(5, 2), pady=6)

entry_min = tk.Entry(delay_frame, font=("Segoe UI", 9, "bold"), bg="#2A2A2A", fg="#FFF", bd=0, width=5, justify='center', insertbackground='white')
entry_min.insert(0, str(delay_min))
entry_min.pack(side='left', pady=6)

lbl_to = tk.Label(delay_frame, text="До:", font=("Segoe UI", 9, "bold"), fg="#B0BEC5", bg="#212121")
lbl_to.pack(side='left', padx=(8, 2), pady=6)

entry_max = tk.Entry(delay_frame, font=("Segoe UI", 9, "bold"), bg="#2A2A2A", fg="#FFF", bd=0, width=5, justify='center', insertbackground='white')
entry_max.insert(0, str(delay_max))
entry_max.pack(side='left', bg="#2A2A2A")

def apply_random_delay():
    global delay_min, delay_max
    try:
        val_min = float(entry_min.get().replace(',', '.'))
        val_max = float(entry_max.get().replace(',', '.'))
        
        if val_min < 0.05: val_min = 0.05
        if val_max < 0.05: val_max = 0.05
        
        if val_min > val_max:
            val_min, val_max = val_max, val_min
            
        delay_min = val_min
        delay_max = val_max
        delay_status.config(text="ОК!", fg="#00E676")
    except ValueError:
        delay_min = 0.1
        delay_max = 0.3
        delay_status.config(text="Ошибка!", fg="#FF1744")
        
    entry_min.delete(0, tk.END)
    entry_min.insert(0, str(delay_min))
    entry_max.delete(0, tk.END)
    entry_max.insert(0, str(delay_max))

apply_btn = tk.Button(
    delay_frame, text="Set", command=apply_random_delay,
    bg="#37474F", fg="#FFF", bd=0, font=("Segoe UI", 8, "bold"), width=5, cursor="hand2"
)
apply_btn.pack(side='left', padx=8)

delay_status = tk.Label(delay_frame, text="", font=("Segoe UI", 9, "bold"), bg="#212121")
delay_status.pack(side='left')

def toggle_minimize():
    global is_minimized
    old_x, old_y = root.winfo_x(), root.winfo_y()
    
    if not is_minimized:
        main_container.pack_forget()
        title_label.pack_forget()
        close_btn.pack_forget()
        
        new_x = max(0, min(old_x, screen_width - MINI_SIZE))
        new_y = max(0, min(old_y, screen_height - MINI_SIZE))
        
        root.geometry(f"{MINI_SIZE}x{MINI_SIZE}+{new_x}+{new_y}")
        top_bar.config(height=MINI_SIZE)
        minimize_btn.config(text="＋", font=("Segoe UI", 14, "bold"), bg="#2E7D32", fg="#FFFFFF")
        minimize_btn.pack(fill='both', expand=True)
        is_minimized = True
    else:
        minimize_btn.pack_forget()
        top_bar.config(height=30)
        
        title_label.pack(side='left', padx=10, pady=5)
        close_btn.pack(side='right', padx=5, pady=5)
        minimize_btn.config(text="－", font=("Segoe UI", 11, "bold"), bg="#262626", fg="#B3B3B3")
        minimize_btn.pack(side='right', padx=5, pady=5)
        
        main_container.pack(fill='both', expand=True, padx=15, pady=10)
        
        new_x = max(0, min(old_x, screen_width - WINDOW_WIDTH))
        new_y = max(0, min(old_y, screen_height - WINDOW_HEIGHT))
        
        root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{new_x}+{new_y}")
        is_minimized = False

close_btn = tk.Button(top_bar, text="✕", command=root.destroy, bg="#262626", fg="#B3B3B3", bd=0, font=("Segoe UI", 10, "bold"), activebackground="#D32F2F", activeforeground="#FFFFFF", width=3)
close_btn.pack(side='right', padx=5, pady=5)

minimize_btn = tk.Button(top_bar, text="－", command=toggle_minimize, bg="#262626", fg="#B3B3B3", bd=0, font=("Segoe UI", 11, "bold"), activebackground="#424242", activeforeground="#FFFFFF", width=3)
minimize_btn.pack(side='right', padx=5, pady=5)

def translate_move_to_russian(move_uci):
    try:
        move = chess.Move.from_uci(move_uci[:4])
        piece = board.piece_type_at(move.from_square)
        piece_name = PIECE_NAMES.get(piece, "Пешка")
        
        if move_uci in ["e1g1", "e8g8"] and piece == chess.KING:
            return "Короткая рокировка"
        if move_uci in ["e1c1", "e8c8"] and piece == chess.KING:
            return "Длинная рокировка"
                
        target_square = chess.square_name(move.to_square)
        suffix = " с превращением" if len(move_uci) == 5 else ""
        return f"{piece_name} на {target_square}{suffix}"
    except:
        return move_uci

def get_square_name(file_idx, rank_idx):
    global my_color
    if my_color == "black":
        file_idx = 7 - file_idx
        rank_idx = 7 - rank_idx
    file_name = chr(ord('a') + file_idx)
    rank_name = str(rank_idx + 1)
    return file_name + rank_name

def get_square_screen_coords(sq_name):
    global board_left, board_top, square_size, my_color
    file_idx = ord(sq_name[0]) - ord('a')
    rank_idx = int(sq_name[1]) - 1
    
    if my_color == "black":
        file_idx = 7 - file_idx
        rank_idx = 7 - rank_idx
    
    x = board_left + int((file_idx + 0.5) * square_size)
    y = board_top + int((7 - rank_idx + 0.5) * square_size)
    return x, y

def click_chess_move(move_uci):
    x1, y1 = get_square_screen_coords(move_uci[:2])
    x2, y2 = get_square_screen_coords(move_uci[2:4])
    
    old_x, old_y = pyautogui.position()
    
    pyautogui.click(x1, y1)   
    time.sleep(0.06)          
    pyautogui.click(x2, y2)   
    
    if len(move_uci) == 5:
        time.sleep(0.15)       
        pyautogui.click(x2, y2) 
        
    pyautogui.moveTo(old_x, old_y)

def detect_last_move_by_vision():
    global board_left, board_top, square_size, board
    if square_size == 0:
        return None
        
    with mss.mss() as sct:
        monitor = {"top": int(board_top), "left": int(board_left), "width": int(square_size * 8), "height": int(square_size * 8)}
        sct_img = sct.grab(monitor)
        img = np.array(sct_img)
        
        hsv = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        hsv = cv2.cvtColor(hsv, cv2.COLOR_BGR2HSV)
        
        lower_highlight = np.array([24, 60, 140])
        upper_highlight = np.array([38, 255, 255])
        mask = cv2.inRange(hsv, lower_highlight, upper_highlight)
        
        highlighted_squares = []
        
        for rank in range(8):
            for file in range(8):
                x_start = int(file * square_size + square_size * 0.20)
                x_end = int(file * square_size + square_size * 0.80)
                y_start = int(rank * square_size + square_size * 0.20)
                y_end = int(rank * square_size + square_size * 0.80)
                
                square_region = mask[y_start:y_end, x_start:x_end]
                
                matching_pixels = np.sum(square_region > 0)
                required_pixels = int((square_size * 0.6) * (square_size * 0.6) * 0.15)
                
                if matching_pixels > required_pixels:
                    sq_name = get_square_name(file, 7 - rank)
                    highlighted_squares.append(sq_name)
                    
        if len(highlighted_squares) == 2:
            opt1 = highlighted_squares[0] + highlighted_squares[1]
            opt2 = highlighted_squares[1] + highlighted_squares[0]
            
            for move_str in [opt1, opt2]:
                try:
                    if chess.Move.from_uci(move_str) in board.legal_moves: return move_str
                except: pass
                try:
                    if chess.Move.from_uci(move_str + "q") in board.legal_moves: return move_str + "q"
                except: pass
                
        if len(highlighted_squares) > 2:
            for sq1 in highlighted_squares:
                for sq2 in highlighted_squares:
                    if sq1 == sq2: continue
                    possible_move = sq1 + sq2
                    try:
                        if chess.Move.from_uci(possible_move) in board.legal_moves:
                            return possible_move
                        if chess.Move.from_uci(possible_move + "q") in board.legal_moves:
                            return possible_move + "q"
                    except:
                        continue
                        
    return None

def auto_analyze():
    global my_color, board, last_processed_move
    if not engine: return
    
    try:
        detected_move = detect_last_move_by_vision()
        
        if detected_move is not None and detected_move != last_processed_move:
            board.push_uci(detected_move)
            last_processed_move = detected_move
            
        engine.set_fen_position(board.fen())
        is_white_turn = board.turn
        
        is_my_turn = (is_white_turn and my_color == "white") or (not is_white_turn and my_color == "black")
        
        if is_my_turn:
            best_move = engine.get_best_move()
            if best_move:
                nice_move = translate_move_to_russian(best_move)
                if not is_minimized:
                    label.config(text=f"Выполняю ход:\n{nice_move}", fg="#81C784")
                
                click_chess_move(best_move)
                board.push_uci(best_move)
                last_processed_move = best_move 
        else:
            if not is_minimized:
                label.config(text="Ожидание хода соперника...", fg="#90A4AE")
            
    except Exception as e:
        if not is_minimized:
            label.config(text="Ошибка синхронизации", fg="#E57373")

def fix_sync():
    global last_processed_move
    try:
        last_processed_move = None 
        if not is_minimized:
            label.config(text="Позиция сброшена!\nЧитаю доску заново...", fg="#FFD54F")
    except:
        pass

def auto_play_loop():
    global auto_mode, delay_min, delay_max
    while auto_mode:
        root.after(0, auto_analyze)
        current_sleep = random.uniform(delay_min, delay_max)
        time.sleep(current_sleep) 

def set_top_left():
    global board_left, board_top
    board_left, board_top = pyautogui.position()
    if not is_minimized:
        label.config(text="Левый верх зафиксирован!\nЖми F8 на правом нижнем углу", fg="#FFD54F")

def set_bottom_right():
    global board_right, board_bottom, square_size
    board_right, board_bottom = pyautogui.position()
    width = board_right - board_left
    square_size = width / 8
    if not is_minimized:
        label.config(text="Доска успешно настроена!\nF3 - Авто-игра, F4 - Один ход", fg="#81C784")

def reset_game():
    global board, auto_mode, last_processed_move
    if auto_mode:
        root.after(0, toggle_auto_mode)
    board = chess.Board()
    last_processed_move = None
    if not is_minimized:
        label.config(text="Доска сброшена! Нажми F4 или F3", fg="#81C784")

def check_hotkeys():
    while True:
        if keyboard.is_pressed('f7'):
            root.after(10, set_top_left)
            time.sleep(0.4)
        if keyboard.is_pressed('f8'):
            root.after(10, set_bottom_right)
            time.sleep(0.4)
        if keyboard.is_pressed('f4'):
            root.after(10, auto_analyze)
            time.sleep(0.1)
        if keyboard.is_pressed('f3'):
            root.after(10, toggle_auto_mode)
            time.sleep(0.5)
        if keyboard.is_pressed('f2'):
            root.after(10, reset_game)
            time.sleep(0.4)
        if keyboard.is_pressed('f9'):  
            root.after(10, fix_sync)
            time.sleep(0.4)
        time.sleep(0.02)

threading.Thread(target=check_hotkeys, daemon=True).start()

drag_x, drag_y = 0, 0
def start_drag(event): 
    global drag_x, drag_y
    drag_x, drag_y = event.x, event.y

def drag(event):
    global is_minimized, screen_width, screen_height
    w = MINI_SIZE if is_minimized else WINDOW_WIDTH
    h = MINI_SIZE if is_minimized else WINDOW_HEIGHT
    
    new_x = root.winfo_x() + (event.x - drag_x)
    new_y = root.winfo_y() + (event.y - drag_y)
    
    final_x = max(0, min(new_x, screen_width - w))
    final_y = max(0, min(new_y, screen_height - h))
    
    root.geometry(f"+{final_x}+{final_y}")

top_bar.bind("<Button-1>", start_drag)
top_bar.bind("<B1-Motion>", drag)
title_label.bind("<Button-1>", start_drag)
title_label.bind("<B1-Motion>", drag)

root.mainloop()
