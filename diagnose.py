"""
diagnose.py
-------------
Kleines Hilfsskript, um herauszufinden, warum Bilder im Memory-Spiel
nicht angezeigt werden (Buchstaben statt echter Bilder).

Einfach im gleichen Ordner wie memory_game.py ausführen:

    python diagnose.py

Es prüft:
  1. ob Pillow (PIL) korrekt importiert werden kann
  2. ob jede einzelne Bilddatei in logoData/ von Pillow geöffnet
     werden kann - und zeigt bei Fehlern die genaue Ursache
"""

import os
import sys

print("=" * 60)
print("Python-Version:", sys.version)
print("Python-Pfad:", sys.executable)
print("=" * 60)

# ---- Schritt 1: Pillow-Import testen --------------------------------------
try:
    import PIL
    from PIL import Image
    print(f"[OK] Pillow ist installiert. Version: {PIL.__version__}")
except Exception as e:
    print("[FEHLER] Pillow konnte NICHT importiert werden!")
    print(f"         Fehlermeldung: {type(e).__name__}: {e}")
    print()
    print("Lösung: im aktivierten venv ausführen:")
    print("    pip uninstall pillow")
    print('    pip install "Pillow<10.0.0"')
    sys.exit(1)

# ---- Schritt 2: pygame testen (nur informativ) ----------------------------
try:
    import pygame
    print(f"[OK] pygame ist installiert. Version: {pygame.__version__}")
except Exception as e:
    print(f"[HINWEIS] pygame nicht verfügbar ({e}) - Spiel läuft dann ohne Ton.")

print("=" * 60)

# ---- Schritt 3: logoData-Ordner finden ------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "logoData")

if not os.path.isdir(DATA_DIR):
    print(f"[FEHLER] Ordner nicht gefunden: {DATA_DIR}")
    sys.exit(1)

print(f"Durchsuche: {DATA_DIR}\n")

IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp")

checked = 0
errors = 0

for root, dirs, files in os.walk(DATA_DIR):
    for fname in files:
        if fname.lower().endswith(IMAGE_EXTS):
            path = os.path.join(root, fname)
            checked += 1
            try:
                with Image.open(path) as img:
                    img.verify()  # prüft, ob Bilddaten gültig sind
                # nach verify() muss man das Bild fuer echte Nutzung neu oeffnen
                with Image.open(path) as img2:
                    img2.convert("RGB")
                print(f"[OK]     {path}  ({img.format}, {img.size})")
            except Exception as e:
                errors += 1
                print(f"[FEHLER] {path}")
                print(f"         -> {type(e).__name__}: {e}")

print()
print("=" * 60)
print(f"Ergebnis: {checked} Bilder geprüft, {errors} davon fehlerhaft.")
if errors == 0 and checked > 0:
    print("Alle Bilder sind grundsätzlich ladbar - das Problem lag vermutlich")
    print("an einer alten/fehlerhaften Pillow-Installation. Bitte")
    print("memory_game.py (aktualisierte Version) erneut versuchen.")
elif checked == 0:
    print("Es wurden GAR KEINE Bilddateien gefunden! Bitte Dateiendungen")
    print(f"prüfen (erlaubt: {IMAGE_EXTS}).")
print("=" * 60)
