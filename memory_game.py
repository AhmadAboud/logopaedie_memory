"""
memory_game.py
----------------
Logopädie-Memory-Spiel (Bild-Ton-Zuordnung) für Kinder.

Erwartete Ordnerstruktur (siehe README.md):

    logoData/
        Menschen/
            Gähnen/
                <ein Bild, z.B. gaehnen.png>
                <eine oder mehrere Audiodateien, z.B. mixkit-cartoon-vocal-1.wav>
            Lachen/
                ...
        Tiere/
            Kuh/
                kuh.png
                kuh.wav
            ...
        Verkehrsmitteln/
            Auto/
                auto.png
                hupe1.wav
                hupe2.wav   <- gibt es mehrere Audiodateien, wird zufällig eine gewählt
            ...

Ablauf:
- Oben wird per Dropdown eine Kategorie gewählt (z.B. "Tiere").
- Das Spiel wählt automatisch 3 zufällige Unterordner (= 3 Begriffe)
  aus dieser Kategorie aus -> 6 Karten (3 Paare).
- Bei jeder Karte: Klick deckt das Bild auf UND spielt eine (bei
  mehreren Dateien zufällig ausgewählte) passende Audiodatei ab.
- Findet das Kind zwei gleiche Karten, bleiben sie aufgedeckt.
- Bei "Neu starten" (oder Kategoriewechsel) werden automatisch neue,
  zufällige Begriffe aus der Kategorie gewählt.

Voraussetzungen:
    pip install -r requirements.txt   (pygame, Pillow)

Start:
    python memory_game.py
"""

import os
import csv
import math
import random
import time
import traceback
import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter import font as tkfont

# ---- optionale Bibliotheken ------------------------------------------------
try:
    import pygame
    _SOUND_AVAILABLE = True
except ImportError:
    _SOUND_AVAILABLE = False

try:
    from PIL import Image, ImageTk, ImageOps
    _PIL_AVAILABLE = True
except ImportError:
    _PIL_AVAILABLE = False


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "data_dir_config.txt")
DEFAULT_DATA_DIR = os.path.join(BASE_DIR, "logoData")
RESULTS_CSV = os.path.join(BASE_DIR, "ergebnisse.csv")
CSV_COLUMNS = [
    "Datum", "Uhrzeit", "Name", "Kategorie",
    "Kartenanzahl", "Gefundene_Paare", "Versuche", "Dauer_Sekunden",
]

IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp")
AUDIO_EXTS = (".wav", ".mp3", ".ogg", ".flac", ".m4a", ".aac")

CARD_BACK_TEXT = "❓"
CARD_BG = "#3F72AF"
CARD_BG_OPEN = "#FFFFFF"
CARD_BG_MATCH = "#8FD694"
WINDOW_BG = "#FDF6EC"
FLIP_BACK_DELAY_MS = 1100
IMAGE_SIZE = 150
DEFAULT_PAIRS_COUNT = 3  # 3 Paare = 6 Karten (Standard)
CARD_COUNT_OPTIONS = [6, 8, 10, 12]  # wählbare Gesamtzahl an Karten
# wie viele Spalten je Gesamtkartenzahl (fürs Raster)
COLS_BY_CARD_COUNT = {6: 3, 8: 4, 10: 5, 12: 4}


# ---------------------------------------------------------------------------
# Datenordner finden / merken
# ---------------------------------------------------------------------------
def load_data_dir():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                path = f.read().strip()
            if path and os.path.isdir(path):
                return path
        except OSError:
            pass
    if os.path.isdir(DEFAULT_DATA_DIR):
        return DEFAULT_DATA_DIR
    return None


def save_data_dir(path):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            f.write(path)
    except OSError:
        pass


# ---------------------------------------------------------------------------
# Ergebnisse als CSV speichern
# ---------------------------------------------------------------------------
def save_result_to_csv(name, category, card_count, pairs_found, attempts, duration_seconds):
    """Hängt eine Zeile mit dem Spielergebnis an ergebnisse.csv an.
    Legt die Datei (mit Kopfzeile) an, falls sie noch nicht existiert."""
    file_exists = os.path.exists(RESULTS_CSV)
    now = datetime.datetime.now()
    row = {
        "Datum": now.strftime("%d.%m.%Y"),
        "Uhrzeit": now.strftime("%H:%M:%S"),
        "Name": name.strip() if name and name.strip() else "Unbekannt",
        "Kategorie": category,
        "Kartenanzahl": card_count,
        "Gefundene_Paare": pairs_found,
        "Versuche": attempts,
        "Dauer_Sekunden": round(duration_seconds, 1),
    }
    try:
        # utf-8-sig, damit Umlaute in Excel korrekt angezeigt werden
        with open(RESULTS_CSV, "a", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, delimiter=";")
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)
        return True
    except OSError:
        return False


# ---------------------------------------------------------------------------
# Ordner einlesen
# ---------------------------------------------------------------------------
def list_subfolders(path):
    try:
        return sorted(
            entry.name for entry in os.scandir(path) if entry.is_dir()
        )
    except OSError:
        return []


def pick_media_for_item(item_path):
    """Wählt (bei mehreren Dateien zufällig) ein Bild und einen Ton aus
    dem Ordner eines Begriffs aus."""
    try:
        files = os.listdir(item_path)
    except OSError:
        return None, None

    images = [f for f in files if f.lower().endswith(IMAGE_EXTS)]
    audios = [f for f in files if f.lower().endswith(AUDIO_EXTS)]

    image = os.path.join(item_path, random.choice(images)) if images else None
    audio = os.path.join(item_path, random.choice(audios)) if audios else None
    return image, audio


def build_item_pool(category_dir):
    """Erstellt eine Liste aller gültigen Begriffe (mit Bild) einer Kategorie.
    Bild und Ton werden hier noch NICHT final ausgewählt, das passiert
    bei jedem Spielstart neu (für Zufallsauswahl bei mehreren Dateien)."""
    pool = []
    for name in list_subfolders(category_dir):
        item_path = os.path.join(category_dir, name)
        # nur aufnehmen, wenn mindestens ein Bild vorhanden ist
        try:
            files = os.listdir(item_path)
        except OSError:
            continue
        has_image = any(f.lower().endswith(IMAGE_EXTS) for f in files)
        if has_image:
            pool.append({"name": name, "path": item_path})
    return pool


# ---------------------------------------------------------------------------
# Ton-Wiedergabe
# ---------------------------------------------------------------------------
class SoundPlayer:
    def __init__(self):
        self.enabled = _SOUND_AVAILABLE
        if self.enabled:
            try:
                pygame.mixer.init()
            except Exception:
                self.enabled = False
        self._cache = {}

    def play(self, path):
        if not self.enabled or not path or not os.path.exists(path):
            return
        try:
            if path not in self._cache:
                self._cache[path] = pygame.mixer.Sound(path)
            self._cache[path].play()
        except Exception:
            pass  # z.B. nicht unterstütztes Format -> einfach stumm bleiben


# ---------------------------------------------------------------------------
# Eine Spielkarte
# ---------------------------------------------------------------------------
class MemoryCard:
    def __init__(self, parent, item, on_click, index, card_font):
        self.item = item  # {"name","image_path","audio_path"}
        self.index = index
        self.matched = False
        self.revealed = False
        self._tk_image = None

        # feste Größe über ein Frame, damit sich das Raster beim
        # Umdrehen (Text -> Bild) nicht verschiebt
        self.frame = tk.Frame(
            parent, width=IMAGE_SIZE + 20, height=IMAGE_SIZE + 20, bg=WINDOW_BG
        )
        self.frame.pack_propagate(False)

        self.button = tk.Button(
            self.frame,
            text=CARD_BACK_TEXT,
            font=card_font,
            bg=CARD_BG,
            fg="white",
            activebackground=CARD_BG,
            relief="raised",
            bd=4,
            command=lambda: on_click(index),
        )
        self.button.pack(fill="both", expand=True)

    def grid(self, **kwargs):
        self.frame.grid(**kwargs)

    def _load_image(self):
        if not _PIL_AVAILABLE:
            print("[Bild-Fehler] Pillow (PIL) ist nicht verfügbar - "
                  "siehe diagnose.py für Details.")
            return None
        if not self.item.get("image_path"):
            print(f"[Bild-Fehler] Kein Bild gefunden für '{self.item['name']}'.")
            return None
        path = self.item["image_path"]
        if not os.path.exists(path):
            print(f"[Bild-Fehler] Datei existiert nicht: {path}")
            return None
        try:
            img = Image.open(path).convert("RGB")
            # Bild vollständig anzeigen (ohne Zuschneiden): proportional
            # verkleinern und mittig auf weißen Hintergrund setzen.
            img.thumbnail((IMAGE_SIZE, IMAGE_SIZE), Image.LANCZOS)
            canvas_img = Image.new("RGB", (IMAGE_SIZE, IMAGE_SIZE), (255, 255, 255))
            offset = ((IMAGE_SIZE - img.width) // 2, (IMAGE_SIZE - img.height) // 2)
            canvas_img.paste(img, offset)
            self._tk_image = ImageTk.PhotoImage(canvas_img)
            return self._tk_image
        except Exception:
            print(f"[Bild-Fehler] Konnte '{path}' nicht laden:")
            traceback.print_exc()
            return None

    def reveal(self):
        self.revealed = True
        tk_img = self._load_image()
        if tk_img is not None:
            self.button.config(image=tk_img, text="", bg=CARD_BG_OPEN)
        else:
            # Fallback, falls Bild nicht geladen werden kann
            self.button.config(image="", text=self.item["name"][:1], bg=CARD_BG_OPEN)

    def hide(self):
        if self.matched:
            return
        self.revealed = False
        self.button.config(image="", text=CARD_BACK_TEXT, bg=CARD_BG)

    def mark_matched(self):
        self.matched = True
        self.button.config(bg=CARD_BG_MATCH, state="disabled")


# ---------------------------------------------------------------------------
# Gewinn-Feuerwerk
# ---------------------------------------------------------------------------
class FireworksWindow(tk.Toplevel):
    """Kleines Zusatzfenster mit animiertem Feuerwerk und Glückwunsch-Text,
    das erscheint, wenn alle Paare gefunden wurden."""

    COLORS = ["#FF595E", "#FFCA3A", "#8AC926", "#1982C4", "#6A4C93", "#FF9F1C", "#FFFFFF"]
    CANVAS_W = 520
    CANVAS_H = 380

    def __init__(self, parent, message="Du hast gewonnen!"):
        super().__init__(parent)
        self.title("🎉 Geschafft! 🎉")
        self.configure(bg="#111122")
        self.resizable(False, False)
        self.transient(parent)

        self.canvas = tk.Canvas(
            self, width=self.CANVAS_W, height=self.CANVAS_H,
            bg="#111122", highlightthickness=0,
        )
        self.canvas.pack()

        self.canvas.create_text(
            self.CANVAS_W // 2, 45,
            text=f"🎉 {message} 🎉",
            fill="white",
            font=("Comic Sans MS", 22, "bold"),
        )

        btn_frame = tk.Frame(self, bg="#111122")
        btn_frame.pack(pady=10)
        tk.Button(
            btn_frame,
            text="Weiterspielen",
            font=("Arial", 12, "bold"),
            command=self.close,
            bg="#F4A259",
            activebackground="#E08E45",
        ).pack()

        self.particles = []
        self._running = True

        self.protocol("WM_DELETE_WINDOW", self.close)
        self._spawn_burst()
        self._animate()

        # zentriert über dem Hauptfenster positionieren
        self.update_idletasks()
        px = parent.winfo_rootx() + (parent.winfo_width() - self.winfo_width()) // 2
        py = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{max(px,0)}+{max(py,0)}")

    def _spawn_burst(self):
        if not self._running or not self.winfo_exists():
            return
        cx = random.randint(80, self.CANVAS_W - 80)
        cy = random.randint(80, 220)
        color = random.choice(self.COLORS)
        n = 26
        for i in range(n):
            angle = (2 * math.pi * i / n) + random.uniform(-0.12, 0.12)
            speed = random.uniform(2.5, 5.5)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            pid = self.canvas.create_oval(
                cx - 3, cy - 3, cx + 3, cy + 3, fill=color, outline=""
            )
            self.particles.append(
                {"id": pid, "x": cx, "y": cy, "vx": vx, "vy": vy, "life": 32}
            )
        self.after(random.randint(550, 950), self._spawn_burst)

    def _animate(self):
        if not self._running or not self.winfo_exists():
            return
        gravity = 0.12
        still_alive = []
        for p in self.particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["vy"] += gravity
            p["life"] -= 1
            if p["life"] <= 0 or p["y"] > self.CANVAS_H:
                self.canvas.delete(p["id"])
            else:
                self.canvas.coords(
                    p["id"], p["x"] - 3, p["y"] - 3, p["x"] + 3, p["y"] + 3
                )
                still_alive.append(p)
        self.particles = still_alive
        self.after(30, self._animate)

    def close(self):
        self._running = False
        self.destroy()


# ---------------------------------------------------------------------------
# Ergebnis-Tabelle (liest ergebnisse.csv und zeigt sie als Tabelle an)
# ---------------------------------------------------------------------------
# Anzeigenamen für die Spaltenüberschriften (lesbarer als die CSV-Header)
COLUMN_DISPLAY_NAMES = {
    "Datum": "Datum",
    "Uhrzeit": "Uhrzeit",
    "Name": "Name",
    "Kategorie": "Kategorie",
    "Kartenanzahl": "Karten",
    "Gefundene_Paare": "Paare",
    "Versuche": "Versuche",
    "Dauer_Sekunden": "Dauer (s)",
}


def read_results_csv():
    """Liest ergebnisse.csv und gibt eine Liste von Dicts zurück
    (neueste Zeile zuerst). Gibt eine leere Liste zurück, wenn die
    Datei nicht existiert oder leer ist."""
    if not os.path.exists(RESULTS_CSV):
        return []
    try:
        with open(RESULTS_CSV, "r", newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f, delimiter=";")
            rows = list(reader)
        rows.reverse()  # neueste zuerst
        return rows
    except OSError:
        return []


class ResultsWindow(tk.Toplevel):
    """Eigenständiges Fenster, das die gespeicherten Ergebnisse aus
    ergebnisse.csv als Tabelle anzeigt - ganz ohne Excel/Office."""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("📊 Gespeicherte Ergebnisse")
        self.configure(bg=WINDOW_BG)
        self.geometry("820x480")
        self.minsize(600, 350)
        self.transient(parent)

        top_bar = tk.Frame(self, bg=WINDOW_BG)
        top_bar.pack(fill="x", padx=10, pady=(10, 0))

        tk.Label(
            top_bar,
            text="Gespeicherte Spielergebnisse",
            font=("Comic Sans MS", 15, "bold"),
            bg=WINDOW_BG,
            fg="#1F3A5F",
        ).pack(side="left")

        tk.Button(
            top_bar, text="🔄 Aktualisieren", command=self._reload,
            bg="#6FA8DC", activebackground="#5B8FC0",
        ).pack(side="right")

        table_frame = tk.Frame(self, bg=WINDOW_BG)
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        columns = CSV_COLUMNS
        self.tree = ttk.Treeview(
            table_frame, columns=columns, show="headings", selectmode="browse"
        )
        for col in columns:
            self.tree.heading(
                col, text=COLUMN_DISPLAY_NAMES.get(col, col),
                command=lambda c=col: self._sort_by(c, False),
            )
            width = 160 if col == "Name" else 100
            self.tree.column(col, width=width, anchor="center")

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        self.summary_label = tk.Label(
            self, text="", font=("Arial", 10), bg=WINDOW_BG, fg="#8A6D3B"
        )
        self.summary_label.pack(pady=(0, 6))

        tk.Button(
            self, text="Schließen", command=self.destroy,
            bg="#F4A259", activebackground="#E08E45",
        ).pack(pady=(0, 10))

        self._reload()

    def _reload(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        rows = read_results_csv()
        if not rows:
            self.summary_label.config(
                text="Noch keine Ergebnisse gespeichert (ergebnisse.csv ist leer "
                     "oder existiert noch nicht - einfach ein Spiel zu Ende spielen)."
            )
            return

        for row in rows:
            values = [row.get(col, "") for col in CSV_COLUMNS]
            self.tree.insert("", "end", values=values)

        self.summary_label.config(
            text=f"{len(rows)} gespeicherte(s) Ergebnis(se)  |  Datei: {RESULTS_CSV}"
        )

    def _sort_by(self, col, descending):
        items = [(self.tree.set(k, col), k) for k in self.tree.get_children("")]

        def sort_key(pair):
            value = pair[0]
            try:
                return (0, float(value.replace(",", ".")))
            except ValueError:
                return (1, value)

        items.sort(key=sort_key, reverse=descending)
        for index, (_, k) in enumerate(items):
            self.tree.move(k, "", index)
        self.tree.heading(col, command=lambda: self._sort_by(col, not descending))


# ---------------------------------------------------------------------------
# Hauptanwendung
# ---------------------------------------------------------------------------
class MemoryGameApp:
    def __init__(self, root, data_dir):
        self.root = root
        self.data_dir = data_dir
        self.root.title("Logopädie Memory – Bild und Ton finden")
        self.root.configure(bg=WINDOW_BG)
        self.root.resizable(True, True)
        self.root.minsize(750, 700)

        self.sound_player = SoundPlayer()

        self.big_font = tkfont.Font(family="Segoe UI", size=13)
        self.card_font = tkfont.Font(family="Segoe UI Emoji", size=40)
        self.title_font = tkfont.Font(family="Comic Sans MS", size=20, weight="bold")

        self.flipped_indices = []
        self.matches_found = 0
        self.attempts = 0
        self.input_locked = False
        self.cards = []
        self.current_category = None
        self.active_pairs_count = DEFAULT_PAIRS_COUNT
        self.start_time = None

        self.categories = list_subfolders(self.data_dir)

        self._build_header()
        self._build_board_area()
        self._build_footer()

        if not self.categories:
            messagebox.showwarning(
                "Keine Kategorien gefunden",
                f"Im Ordner\n{self.data_dir}\n wurden keine Unterordner "
                "(Kategorien) gefunden. Bitte Ordnerstruktur prüfen.",
            )
        else:
            self.category_var.set(self.categories[0])
            self.new_game(self.categories[0])

        warnings = []
        if not _PIL_AVAILABLE:
            warnings.append(
                "Pillow (PIL) fehlt/fehlerhaft – Bilder werden nicht angezeigt! "
                "Bitte 'python diagnose.py' ausführen."
            )
        if not self.sound_player.enabled:
            warnings.append(
                "'pygame' nicht installiert – Spiel läuft ohne Ton. "
                "(pip install pygame)"
            )
        if warnings:
            self.status_label.config(text=" | ".join(warnings), fg="#B0413E")

    # ---------------------------------------------------------------- UI ---
    def _build_header(self):
        header = tk.Frame(self.root, bg=WINDOW_BG)
        header.pack(pady=(15, 5))
        tk.Label(
            header,
            text="Finde die zwei passenden Bilder! 🧠",
            font=self.title_font,
            bg=WINDOW_BG,
            fg="#1F3A5F",
        ).pack(pady=(0, 10))

        selector = tk.Frame(header, bg=WINDOW_BG)
        selector.pack()
        tk.Label(
            selector, text="Kategorie:", font=self.big_font, bg=WINDOW_BG, fg="#1F3A5F"
        ).pack(side="left", padx=(0, 8))

        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(
            selector,
            textvariable=self.category_var,
            values=self.categories,
            state="readonly",
            font=self.big_font,
            width=22,
        )
        self.category_combo.pack(side="left")
        self.category_combo.bind("<<ComboboxSelected>>", self._on_category_change)

        tk.Label(
            selector, text="  Anzahl Bilder:", font=self.big_font, bg=WINDOW_BG, fg="#1F3A5F"
        ).pack(side="left", padx=(16, 8))

        self.card_count_var = tk.StringVar(value=str(DEFAULT_PAIRS_COUNT * 2))
        self.card_count_combo = ttk.Combobox(
            selector,
            textvariable=self.card_count_var,
            values=[str(n) for n in CARD_COUNT_OPTIONS],
            state="readonly",
            font=self.big_font,
            width=4,
        )
        self.card_count_combo.pack(side="left")
        self.card_count_combo.bind("<<ComboboxSelected>>", self._on_card_count_change)

        name_row = tk.Frame(header, bg=WINDOW_BG)
        name_row.pack(pady=(10, 0))
        tk.Label(
            name_row, text="Name des Kindes:", font=self.big_font, bg=WINDOW_BG, fg="#1F3A5F"
        ).pack(side="left", padx=(0, 8))

        self.child_name_var = tk.StringVar()
        self.child_name_entry = tk.Entry(
            name_row, textvariable=self.child_name_var, font=self.big_font, width=24
        )
        self.child_name_entry.pack(side="left")

    def _build_board_area(self):
        self.board_container = tk.Frame(self.root, bg=WINDOW_BG)
        self.board_container.pack(padx=20, pady=15)

    def _build_footer(self):
        footer = tk.Frame(self.root, bg=WINDOW_BG)
        footer.pack(pady=(0, 15))

        self.progress_label = tk.Label(
            footer, text="", font=self.big_font, bg=WINDOW_BG, fg="#1F3A5F"
        )
        self.progress_label.pack()

        self.status_label = tk.Label(
            footer, text="", font=("Arial", 10), bg=WINDOW_BG, fg="#8A6D3B"
        )
        self.status_label.pack(pady=(4, 8))

        buttons_row = tk.Frame(footer, bg=WINDOW_BG)
        buttons_row.pack()

        self.repeat_button = tk.Button(
            buttons_row,
            text="🔁 Nochmal hören",
            font=("Arial", 12, "bold"),
            command=self._on_repeat_click,
            bg="#6FA8DC",
            activebackground="#5B8FC0",
            state="disabled",
        )
        self.repeat_button.pack(side="left", padx=(0, 10))

        tk.Button(
            buttons_row,
            text="🔄 Neu starten (neue Bilder)",
            font=("Arial", 12, "bold"),
            command=self._on_restart_click,
            bg="#F4A259",
            activebackground="#E08E45",
        ).pack(side="left", padx=(0, 10))

        tk.Button(
            buttons_row,
            text="📊 Ergebnisse anzeigen",
            font=("Arial", 12, "bold"),
            command=self._on_show_results_click,
            bg="#9B8DC4",
            activebackground="#8678B5",
            fg="white",
        ).pack(side="left")

    def _progress_text(self):
        return (
            f"Kategorie: {self.current_category}    |    "
            f"Gefundene Paare: {self.matches_found} / {self.active_pairs_count}    |    "
            f"Versuche: {self.attempts}"
        )

    # ------------------------------------------------------------ Events ---
    def _on_category_change(self, _event=None):
        self.new_game(self.category_var.get())

    def _on_card_count_change(self, _event=None):
        if self.current_category:
            self.new_game(self.current_category)

    def _on_restart_click(self):
        if self.current_category:
            self.new_game(self.current_category)

    def _on_show_results_click(self):
        ResultsWindow(self.root)

    # -------------------------------------------------------- Spielaufbau ---
    def new_game(self, category_name):
        """Baut ein neues Spielfeld mit zufällig gewählten Begriffen
        (und bei mehreren Dateien zufälligem Bild/Ton) aus der gegebenen
        Kategorie auf. Die Anzahl der Karten richtet sich nach der
        Auswahl im 'Anzahl Bilder'-Dropdown."""
        self.current_category = category_name
        category_dir = os.path.join(self.data_dir, category_name)
        pool = build_item_pool(category_dir)

        if not pool:
            messagebox.showwarning(
                "Keine Begriffe gefunden",
                f"In der Kategorie '{category_name}' wurden keine gültigen "
                "Unterordner mit Bildern gefunden.",
            )
            return

        try:
            desired_card_count = int(self.card_count_var.get())
        except (ValueError, AttributeError):
            desired_card_count = DEFAULT_PAIRS_COUNT * 2
        desired_pairs_count = desired_card_count // 2

        pairs_count = min(desired_pairs_count, len(pool))
        if pairs_count < desired_pairs_count:
            self.status_label.config(
                text=f"Hinweis: Kategorie hat nur {len(pool)} Begriffe "
                     f"(statt {desired_pairs_count})."
            )
        else:
            self.status_label.config(text="")
        self.active_pairs_count = pairs_count

        chosen = random.sample(pool, k=pairs_count)

        # für jeden gewählten Begriff Bild/Ton (zufällig, falls mehrere) auswählen
        prepared_items = []
        for entry in chosen:
            image_path, audio_path = pick_media_for_item(entry["path"])
            prepared_items.append(
                {"name": entry["name"], "image_path": image_path, "audio_path": audio_path}
            )

        pairs = prepared_items * 2
        random.shuffle(pairs)

        # altes Spielfeld entfernen
        for widget in self.board_container.winfo_children():
            widget.destroy()

        self.cards = []
        self.flipped_indices = []
        self.matches_found = 0
        self.attempts = 0
        self.input_locked = False
        self.start_time = time.time()
        self.repeat_button.config(state="disabled")

        total_cards = len(pairs)
        cols = COLS_BY_CARD_COUNT.get(total_cards, 4)
        for i, item in enumerate(pairs):
            card = MemoryCard(self.board_container, item, self.on_card_click, i, self.card_font)
            row, col = divmod(i, cols)
            card.grid(row=row, column=col, padx=12, pady=12)
            self.cards.append(card)

        self.progress_label.config(text=self._progress_text())

    # ------------------------------------------------------------ Logik ---
    def on_card_click(self, index):
        if self.input_locked:
            return
        card = self.cards[index]
        if card.matched or card.revealed:
            return

        card.reveal()
        self.sound_player.play(card.item.get("audio_path"))
        self.flipped_indices.append(index)

        if len(self.flipped_indices) == 1:
            # genau eine Karte aufgedeckt -> Ton kann vor der 2. Wahl
            # beliebig oft wiederholt werden (zählt NICHT als Versuch)
            self.repeat_button.config(state="normal")
        elif len(self.flipped_indices) == 2:
            self.repeat_button.config(state="disabled")
            self.attempts += 1
            self.progress_label.config(text=self._progress_text())
            self.input_locked = True
            self.root.after(450, self._check_match)

    def _on_repeat_click(self):
        """Spielt den Ton der zuerst aufgedeckten (noch offenen) Karte
        erneut ab - zählt bewusst NICHT als neuer Versuch."""
        if len(self.flipped_indices) != 1:
            return
        card = self.cards[self.flipped_indices[0]]
        self.sound_player.play(card.item.get("audio_path"))

    def _check_match(self):
        i1, i2 = self.flipped_indices
        card1, card2 = self.cards[i1], self.cards[i2]

        if card1.item["name"] == card2.item["name"]:
            card1.mark_matched()
            card2.mark_matched()
            self.matches_found += 1
            self.status_label.config(
                text=f"Super! Das ist {card1.item['name']}! 🎉", fg="#2E7D32"
            )
            self.flipped_indices = []
            self.input_locked = False
            self.progress_label.config(text=self._progress_text())
            if self.matches_found == self.active_pairs_count:
                self._on_win()
        else:
            self.status_label.config(
                text="Das war noch nicht gleich – versuch's nochmal!", fg="#B0413E"
            )
            self.root.after(FLIP_BACK_DELAY_MS, self._hide_unmatched)

    def _hide_unmatched(self):
        for i in self.flipped_indices:
            self.cards[i].hide()
        self.flipped_indices = []
        self.input_locked = False

    def _on_win(self):
        self.repeat_button.config(state="disabled")
        duration = time.time() - self.start_time if self.start_time else 0.0
        name = self.child_name_var.get().strip()

        saved = save_result_to_csv(
            name=name,
            category=self.current_category,
            card_count=self.active_pairs_count * 2,
            pairs_found=self.matches_found,
            attempts=self.attempts,
            duration_seconds=duration,
        )

        win_message = f"{name}, Du hast gewonnen!" if name else "Du hast gewonnen!"
        status_text = "🏆 Klasse gemacht! Du hast alle Paare gefunden!"
        status_text += (
            "  (Ergebnis in ergebnisse.csv gespeichert)"
            if saved else "  (Hinweis: Ergebnis konnte nicht gespeichert werden)"
        )
        self.status_label.config(text=status_text, fg="#2E7D32")

        FireworksWindow(self.root, message=win_message)


# ---------------------------------------------------------------------------
def resolve_data_dir():
    """Ermittelt den logoData-Ordner; fragt bei Bedarf den Benutzer."""
    data_dir = load_data_dir()
    if data_dir:
        return data_dir

    # kein Ordner bekannt -> Benutzer fragen
    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo(
        "Datenordner auswählen",
        "Bitte wählen Sie im nächsten Fenster den Ordner 'logoData' "
        "(mit den Unterordnern Menschen/Tiere/Verkehrsmitteln) aus.",
    )
    chosen = filedialog.askdirectory(title="logoData-Ordner auswählen")
    root.destroy()

    if chosen and os.path.isdir(chosen):
        save_data_dir(chosen)
        return chosen
    return None


def main():
    data_dir = resolve_data_dir()
    if not data_dir:
        messagebox.showerror(
            "Kein Datenordner",
            "Es wurde kein gültiger Datenordner ausgewählt. Das Programm wird beendet.",
        )
        return

    root = tk.Tk()
    MemoryGameApp(root, data_dir)
    root.mainloop()


if __name__ == "__main__":
    main()
