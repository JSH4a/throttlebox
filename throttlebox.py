import tkinter as tk
from tkinter import messagebox
import threading
import time
import ctypes
import pydivert

# Global variable for target download rate
TARGET_DOWNLOAD_RATE = 5_000  # Default value in bytes/sec

# Unit multipliers
UNIT_MULTIPLIERS = {
    "Bytes (B/s)": 1,
    "Kilobytes (KB/s)": 1_000,
    "Kibibytes (KiB/s)": 1_024,
    "Megabytes (MB/s)": 1_000_000,
    "Mebibytes (MiB/s)": 1_048_576
}

# Check for admin rights (Windows only)
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

# Function to update bandwidth from UI
def update_bandwidth():
    global TARGET_DOWNLOAD_RATE
    try:
        value = float(bandwidth_entry.get())
        unit = unit_var.get()
        multiplier = UNIT_MULTIPLIERS.get(unit, 1)
        TARGET_DOWNLOAD_RATE = int(value * multiplier)
        status_label.config(text=f"Set to {value} {unit} → {TARGET_DOWNLOAD_RATE:,} B/s")
    except ValueError:
        messagebox.showerror("Invalid Input", "Please enter a valid number.")

# Background thread for packet processing
def start_packet_throttle():
    global TARGET_DOWNLOAD_RATE
    bytes_allowed = 0
    last_time = time.time()

    with pydivert.WinDivert("inbound", layer=pydivert.Layer.NETWORK) as w:
        for packet in w:
            now = time.time()
            elapsed = now - last_time
            bytes_allowed += elapsed * TARGET_DOWNLOAD_RATE
            last_time = now

            packet_len = len(packet.raw)

            if bytes_allowed >= packet_len:
                bytes_allowed -= packet_len
                w.send(packet)
            else:
                sleep_time = (packet_len - bytes_allowed) / TARGET_DOWNLOAD_RATE
                time.sleep(sleep_time)
                bytes_allowed = 0
                w.send(packet)

# ---------- UI Setup ----------

# Colors and styles
BG_COLOR = "#1e1e1e"
FG_COLOR = "#ffffff"
ACCENT_COLOR = "#61dafb"
WARNING_COLOR = "#ff4c4c"
FONT = ("Consolas", 11)

root = tk.Tk()
root.title("Throttlebox")
root.configure(bg=BG_COLOR)
root.geometry("400x270")

# Title
tk.Label(root, text="Throttlebox", fg=ACCENT_COLOR, bg=BG_COLOR,
         font=("Consolas", 14, "bold")).pack(pady=(15, 5))

# Bandwidth input
tk.Label(root, text="Enter Bandwidth Value:", fg=FG_COLOR, bg=BG_COLOR,
         font=FONT).pack(pady=(10, 2))

bandwidth_entry = tk.Entry(root, font=FONT, justify="center", bg="#2a2a2a", fg=FG_COLOR,
                           insertbackground=FG_COLOR, highlightbackground="#444", relief="flat")
bandwidth_entry.insert(0, "5")
bandwidth_entry.pack(pady=(0, 5), ipadx=10, ipady=5)

# Unit dropdown
unit_var = tk.StringVar(value="Kilobytes (KB/s)")
unit_menu = tk.OptionMenu(root, unit_var, *UNIT_MULTIPLIERS.keys())
unit_menu.config(bg="#2a2a2a", fg=FG_COLOR, font=FONT, highlightthickness=0, relief="flat",
                 activebackground="#3b3b3b", activeforeground=FG_COLOR)
unit_menu["menu"].config(bg="#2a2a2a", fg=FG_COLOR, font=FONT)
unit_menu.pack(pady=(0, 10))

# Apply button
def on_enter(e): apply_btn.config(bg="#3b3b3b")
def on_leave(e): apply_btn.config(bg="#2a2a2a")

apply_btn = tk.Button(root, text="Apply Bandwidth", command=update_bandwidth, font=FONT,
                      fg=FG_COLOR, bg="#2a2a2a", activebackground="#3b3b3b", relief="flat",
                      cursor="hand2")
apply_btn.pack(pady=(0, 10), ipadx=5, ipady=2)
apply_btn.bind("<Enter>", on_enter)
apply_btn.bind("<Leave>", on_leave)

# Status message
status_label = tk.Label(root, text="Bandwidth set to default.", fg=ACCENT_COLOR,
                        bg=BG_COLOR, font=FONT)
status_label.pack(pady=(5, 10))

# Admin warning if needed
if not is_admin():
    warning_label = tk.Label(
        root,
        text="⚠️ Please run as Administrator!",
        fg=WARNING_COLOR,
        bg=BG_COLOR,
        font=("Consolas", 10, "bold")
    )
    warning_label.pack(pady=(0, 10))

# Start the packet processing in a thread
threading.Thread(target=start_packet_throttle, daemon=True).start()

# Launch the UI
root.mainloop()
