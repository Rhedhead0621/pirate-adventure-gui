import tkinter as tk
from tkinter import scrolledtext, ttk
import random
from PIL import Image, ImageTk, ImageEnhance
import threading
import time
import sys
import os
import importlib.util

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

game_data_path = resource_path("game_data.py")
spec = importlib.util.spec_from_file_location("game_data", game_data_path)
game_data = importlib.util.module_from_spec(spec)
spec.loader.exec_module(game_data)

islands = game_data.islands
clue_map = game_data.clue_map
parrot_comments = game_data.parrot_comments
milestone_badges = game_data.milestone_badges

# === GAME STATE ===
player_name = "Anna"
shells_collected = 0
sparkle_points = 0
treasure_found = 0
turn_count = 0
ghostly_badge = False
next_clue_island = None
visited_islands = set()
clue_count = 0
secret_island_unlocked = False
secret_island_visited = False
anne_bonny_seen = False
earned_badges = set()

# === GUI SETUP ===
root = tk.Tk()
root.title("Pirate Adventure – Full GUI Edition")
root.geometry("760x700")
root.config(bg="#f0f8ff")

# === FADE-IN/OUT FUNCTION ===
def fade_image(path, duration=1000):
    fade_win = tk.Toplevel(root)
    fade_win.overrideredirect(True)
    fade_win.attributes('-topmost', True)
    fade_win.configure(bg='')
    fade_win.geometry("160x200+550+350")

    img = Image.open(path).resize((160, 200)).convert("RGBA")
    label = tk.Label(fade_win, bg="#f0f8ff")
    label.pack()

    def fade():
        for alpha in range(0, 255, 15):
            faded = img.copy()
            faded.putalpha(alpha)
            tkimg = ImageTk.PhotoImage(faded)
            label.config(image=tkimg)
            label.image = tkimg
            time.sleep(0.05)
        time.sleep(2)
        for alpha in reversed(range(0, 255, 15)):
            faded = img.copy()
            faded.putalpha(alpha)
            tkimg = ImageTk.PhotoImage(faded)
            label.config(image=tkimg)
            label.image = tkimg
            time.sleep(0.05)
        fade_win.destroy()

    threading.Thread(target=fade, daemon=True).start()

# === MAP DISPLAY ===
map_display = tk.Label(root, text="🗺️ Trail Map: [❓ ❓ ❓ ❓ ❓ ❓]", bg="#f0f8ff", font=("Courier", 12))
map_display.pack(pady=5)

def update_map():
    symbols = []
    for i in range(6):
        sym = "🟩" if i in visited_islands else "❓"
        symbols.append(sym)
    map_display.config(text=f"🗺️ Trail Map: [{' '.join(symbols)}]")

# === PROGRESS BARS ===
progress_frame = tk.Frame(root, bg="#f0f8ff")
progress_frame.pack(pady=5)

def create_progress(label_text, row):
    label = tk.Label(progress_frame, text=label_text, bg="#f0f8ff", font=("Arial", 10, "bold"))
    label.grid(row=row, column=0, sticky="w")
    bar = ttk.Progressbar(progress_frame, orient="horizontal", length=500, mode="determinate")
    bar.grid(row=row, column=1, padx=10, pady=2)
    return bar

sparkle_bar = create_progress("✨ Sparkle Points:", 0)
shell_bar = create_progress("🐚 Shells Collected:", 1)
treasure_bar = create_progress("🪙 Treasure Found:", 2)

# === STATUS BOX ===
status_frame = tk.Frame(root, bg="#f0f8ff")
status_frame.pack(pady=5)

status_label = tk.Label(
    status_frame,
    text="🏆 Status:\n👻 Ghostly Badge: ❌\n💀 Anne Bonny Found: ❌",
    bg="#f0f8ff",
    font=("Arial", 10),
    justify="left"
)
status_label.pack()

# === CHAT LOG ===
chat_log = scrolledtext.ScrolledText(root, width=80, height=18, wrap=tk.WORD, bg="white", font=("Courier", 10))
chat_log.pack(pady=10)

# === FUNCTIONS ===
def log(msg):
    chat_log.insert(tk.END, msg + "\n")
    chat_log.see(tk.END)

def update_bars():
    sparkle_bar["value"] = min(sparkle_points, 30)
    shell_bar["value"] = min(shells_collected, 30)
    treasure_bar["value"] = min(treasure_found, 30)

def update_status():
    ghost = "✅" if ghostly_badge else "❌"
    anne = "✅" if clue_count > 0 else "❌"

    status_label.config(
        text=f"🏆 Status:\n👻 Ghostly Badge: {ghost}\n💀 Anne Bonny Found: {anne}"
    )

def try_unlock_secret():
    global secret_island_unlocked
    if not secret_island_unlocked:
        if clue_count >= 2 or sparkle_points >= 20 or len(visited_islands) == 6:
            secret_island_unlocked = True
            log("🌫️ A new trail emerges from the mist... 'Whispering Wreckage ⚓🌫️' is now visible!")
            secret_button.grid(row=2, column=1, padx=5, pady=5)

def start_game():
    global shells_collected, sparkle_points, treasure_found, turn_count
    global ghostly_badge, next_clue_island, visited_islands, clue_count
    global secret_island_unlocked, secret_island_visited
    global anne_bonny_seen, earned_badges
    shells_collected = 0
    sparkle_points = 0
    treasure_found = 0
    turn_count = 0
    ghostly_badge = False
    next_clue_island = None
    visited_islands = set()
    clue_count = 0
    secret_island_unlocked = False
    secret_island_visited = False
    anne_bonny_seen = False
    earned_badges.clear()
    secret_button.grid_remove()
    log(f"\n🏴‍☠️ Captain {player_name}, your voyage begins!")
    log("⛵ Set sail, explore islands, and chase hidden treasures across the sea...")
    log("🦜 Squawkles is watching... try not to disappoint him.\n")
    log("⚓ Choose your first destination wisely...\n")
    fade_image(resource_path("ship_near_land.png"))
    update_map()
    update_bars()
    update_status()    
    start_button.config(state=tk.DISABLED)
    
    for button in island_buttons:
        button.config(state=tk.NORMAL)
    end_button.config(state=tk.NORMAL)

def explore_island(island_name):
    global turn_count, shells_collected, sparkle_points, treasure_found, ghostly_badge, next_clue_island, clue_count, anne_bonny_seen, earned_badges
    turn_count += 1
    index = islands.index(island_name)
    visited_islands.add(index)
    update_map()
    log(f"\n🌊 Turn {turn_count}: You sail to {island_name}")

    if next_clue_island == island_name:
        sparkle_points += 2
        log("✨ You followed Anne Bonny’s clue correctly! +2 sparkle!")
        next_clue_island = None

    if island_name == "Cursed Coral Cove 🐚" and (not anne_bonny_seen or random.randint(1, 2) == 1):
        log("\n💀 The mist thickens... Anne Bonny appears!")
        fade_image(resource_path("anne_bonny.png"))
        anne_bonny_seen = True

        clue_count += 1        
        
        # Determine blessing chance
        if not ghostly_badge:
            success_chance = 0.7
        else:
            success_chance = 0.4
        
        if random.random() < success_chance:
            sparkle_points += 1
            ghostly_badge = True
            next_clue_island = random.choice([i for i in islands if i != "Cursed Coral Cove 🐚"])
            log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            log("👻 Anne Bonny blesses you with +1 sparkle and a ghostly badge!")
            log(f"🔮 She whispers: '{clue_map[next_clue_island]}'")
            log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        else:
            sparkle_points -= 1
            log("*'You’re not worthy of this cove's secrets...'* (-1 sparkle)")

    update_status()
    sparkle = 1
    shell = 2
    treasure = 1
    sparkle_points += sparkle
    shells_collected += shell
    treasure_found += treasure

    if random.randint(1, 2) == 1:
        log(random.choice(parrot_comments))

    if shells_collected >= 10:
        sparkle_points += 1
        shells_collected -= 10
        log("💰 Traded 10 shells for +1 sparkle!")
    if treasure_found >= 5:
        sparkle_points += 1
        treasure_found -= 5
        log("💎 Traded 5 treasure for +1 sparkle!")

    for points, badge in reversed(milestone_badges):
        if sparkle_points >= points and badge not in earned_badges:
            log(f"🏆 Milestone Badge Earned: {badge}")
            earned_badges.add(badge)
            break

    update_bars()
    try_unlock_secret()
    log(f"📊 Current Totals → ✨ {sparkle_points} | 🐚 {shells_collected} | 🪙 {treasure_found}")

def secret_island():
    global sparkle_points, secret_island_visited
    if secret_island_visited:
        log("\n🦜 Squawkles squawks: 'Ye already picked this place clean, Cap’n!'")
        fade_image(resource_path("squawkles.png"))
        return
    secret_island_visited = True
    log("\n🌫️ You sail into the Whispering Wreckage...")
    log("👑 A ghostly voice echoes: 'You have found what few dare dream.'")
    sparkle_bonus = 5
    sparkle_points += sparkle_bonus
    log(f"💎 A spectral treasure chest bursts open! +{sparkle_bonus} sparkle!")
    fade_image(resource_path("treasure.png"))
    log("✨ Your true pirate name glows in light: *Captain Starshade the Undaunted* 🫧")
    update_bars()
    update_status()

def end_voyage():
    log("\n🛳️ You sail back to port...")
    fade_image(resource_path("ship_at_dock.png"))
    log(f"✨ Final Sparkle: {sparkle_points} | 🐚 Shells: {shells_collected} | 🪙 Treasure: {treasure_found}")
    if ghostly_badge:
        log("👻 Bonus Badge Earned: Ghost-Touched by Anne Bonny")
    else:
        log("🪦 No ghostly badge this time...")
    for button in island_buttons:
        button.config(state=tk.DISABLED)
    end_button.config(state=tk.DISABLED)
    start_button.config(state=tk.NORMAL)

# === BUTTONS ===
button_frame = tk.Frame(root, bg="#f0f8ff")
button_frame.pack()

start_button = tk.Button(button_frame, text="Start Sailing", command=start_game, bg="#4CAF50", fg="white", padx=10, pady=5)
start_button.grid(row=0, column=0, padx=5)

end_button = tk.Button(button_frame, text="End Voyage", command=end_voyage, bg="#9C27B0", fg="white", padx=10, pady=5)
end_button.grid(row=0, column=1, padx=5)

# === ISLAND BUTTONS ===
island_buttons = []
island_frame = tk.Frame(root, bg="#f0f8ff")
island_frame.pack(pady=5)

for idx, name in enumerate(islands):
    b = tk.Button(island_frame, text=name, command=lambda n=name: explore_island(n), padx=8, pady=4)
    b.grid(row=idx//3, column=idx%3, padx=5, pady=5)
    island_buttons.append(b)

secret_button = tk.Button(island_frame, text="Whispering Wreckage ⚓🌫️", command=secret_island, bg="#555", fg="white", padx=8, pady=4)
secret_button.grid(row=2, column=1, padx=5, pady=5)
secret_button.grid_remove()

# === RUN ===
log(f"\n🏴‍☠️ Welcome aboard, Captain {player_name}! Click 'Start Sailing' to begin your adventure!\n")
update_bars()
update_map()
root.mainloop()
