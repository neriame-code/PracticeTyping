import time
import datetime
import os
import csv
import sys
import shutil

# OS判定
IS_WINDOWS = (os.name == 'nt')

if IS_WINDOWS:
    import msvcrt
else:
    import tty
    import termios

# スクリプトファイル(.py)が存在するディレクトリの絶対パスを取得
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

REAL_FILE = os.path.join(BASE_DIR, 'typing_practice.txt')
SAMPLE_FILE = os.path.join(BASE_DIR, 'typing_practice_sample.txt')
OUTPUT_FILE = os.path.join(BASE_DIR, 'typing_log.csv')

# ユーザー用のファイルが存在せず、かつサンプルがある場合はコピーを作成
if not os.path.exists(REAL_FILE) and os.path.exists(SAMPLE_FILE):
    try:
        shutil.copy(SAMPLE_FILE, REAL_FILE)
        print(f"初回セットアップ")
        print(f" {SAMPLE_FILE} をコピーして{REAL_FILE} を作成しました。")
        time.sleep(1)
    except Exception as e:
        print(f"セットアップエラー: {e}")

# 読み込むファイルは常に REAL_FILEsにする
INPUT_FILE = REAL_FILE
OUTPUT_FILE = os.path.join(BASE_DIR, 'typing_log.csv')

CONTEXT_LINES = 3

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    GRAY = '\033[90m'
    RESET = '\033[0m'
    BG_RED = '\033[41m'

class GetCh:
    """OSごとのキー入力処理を吸収するクラス"""
    def __init__(self):
        pass

    def __call__(self):
        if IS_WINDOWS:
            try:
                char = msvcrt.getwch()
            except:
                char = msvcrt.getch().decode('utf-8')
            if char == '\x03': # Ctrl+C
                print("\n中断しました。")
                sys.exit()
            return char
        else:
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(sys.stdin.fileno())
                ch = sys.stdin.read(1)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            
            if ch == '\x03': # Ctrl+C
                print("\n中断しました。")
                sys.exit()
            return ch

get_key = GetCh()

def load_text(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return [line.rstrip('\n') for line in f.readlines()]
    except FileNotFoundError:
        print(f"エラー: {filename} が見つかりません。")
        print(f"参照場所: {filename}") # デバッグ用にパスを表示
        return []

def clear_screen():
    os.system('cls' if IS_WINDOWS else 'clear')

def save_log(misses, duration):
    today = datetime.datetime.now().strftime('%Y/%m/%d')
    
    file_exists = os.path.isfile(OUTPUT_FILE)
    try:
        with open(OUTPUT_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['Date', 'MissCount', 'Time(sec)'])
            writer.writerow([today, misses, f"{duration:.2f}"])
        print(f"\n結果を {OUTPUT_FILE} に保存しました。")
    except Exception as e:
        print(f"\n保存エラー: {e}")

def play_line_realtime(target_line, current_misses):
    stripped_part = target_line.lstrip()
    indent_len = len(target_line) - len(stripped_part)
    indent_str = target_line[:indent_len]

    miss_count = 0
    
    sys.stdout.write(f"\r{indent_str}{Colors.GRAY}{stripped_part}{Colors.RESET}")
    sys.stdout.flush()
    
    for i, target_char in enumerate(stripped_part):
        while True:
            completed = stripped_part[:i]
            remain = stripped_part[i+1:] if i+1 < len(stripped_part) else ""
            
            display_str = (
                f"\r{indent_str}"
                f"{Colors.GREEN}{completed}{Colors.RESET}"
                f"{Colors.GRAY}{target_char}{remain}{Colors.RESET}"
            )
            sys.stdout.write(display_str)
            
            move_len = indent_len + i
            if move_len > 0:
                sys.stdout.write(f"\r\033[{move_len}C")
            else:
                sys.stdout.write(f"\r")
            
            sys.stdout.flush()

            user_char = get_key()
            
            if user_char == target_char:
                break
            else:
                miss_count += 1
                sys.stdout.write(f"{Colors.BG_RED}{target_char}{Colors.RESET}")
                sys.stdout.flush()
                time.sleep(0.1)
    
    return miss_count

def main():
    if IS_WINDOWS:
        os.system('') 
    
    lines = load_text(INPUT_FILE)
    if not lines:
        print("テキストファイル読み込みに失敗しました。終了します。")
        get_key()
        return

    clear_screen()
    print("=== タイピング練習 ===")
    print("・インデントは自動入力されます")
    print("・間違えると進めません")
    print("・中断は Ctrl+C")
    print("何かキーを押して開始...")
    get_key()

    total_misses = 0
    start_time = time.time()

    for i, target_line in enumerate(lines):
        clear_screen()
        
        start_idx = max(0, i - CONTEXT_LINES)
        for idx in range(start_idx, i):
            print(f"   {lines[idx]}")
        
        line_misses = play_line_realtime(target_line, total_misses)
        total_misses += line_misses
        
        print() 

    end_time = time.time()
    duration = end_time - start_time

    print(f"\n\n=== 練習終了！ ===")
    print(f"かかった時間: {duration:.2f} 秒")
    print(f"総ミスタイプ数: {total_misses}")
    
    save_log(total_misses, duration)
    print("終了するには何かキーを押してください...")
    get_key()

if __name__ == "__main__":
    if IS_WINDOWS and len(sys.argv) == 1:
        import subprocess
        # Windowsでの自動起動時もパスを正しく渡す必要があるため sys.argv[0] を使用
        command = f'start "Typing Practice" cmd /k "{sys.executable}" "{sys.argv[0]}" launch_mode'
        subprocess.run(command, shell=True)
    else:
        try:
            main()
        except KeyboardInterrupt:
            pass