# Logopädie-Memory (Bild-Ton-Zuordnung mit Kategorien)

Tkinter-Spiel für logopädische Übungen: Nach Auswahl einer Kategorie
(z. B. "Tiere") zeigt das Spiel sechs verdeckte Karten (= 3 zufällig
gewählte Begriffe). Klickt das Kind eine Karte an, wird das Bild
aufgedeckt und ein passender Ton abgespielt (Tierlaut, Geräusch,
Lautäußerung o. Ä.). Ziel: zwei zusammengehörige Karten finden – das
trainiert Gedächtnis, Höraufmerksamkeit und Bild-Wort-Zuordnung.

## Voraussetzte Ordnerstruktur

Das Spiel liest Ihre eigenen Bild-/Tondateien direkt von der
Festplatte ein, genau in der Struktur, die Sie bereits angelegt haben:

```
logopaedie_memory/
├── memory_game.py
├── requirements.txt
├── README.md
└── logoData/
    ├── Menschen/
    │   ├── Gähnen/
    │   │   ├── gaehnen.png              <- ein Bild
    │   │   └── mixkit-cartoon-vocal....wav   <- ein oder mehrere Töne
    │   ├── Lachen/
    │   │   ├── lachen.png
    │   │   └── lachen.wav
    │   └── ... (weitere Begriffe)
    ├── Tiere/
    │   ├── Kuh/
    │   │   ├── kuh.png
    │   │   └── kuh.wav
    │   └── ... (weitere Begriffe)
    └── Verkehrsmitteln/
        ├── Auto/
        │   ├── auto.png
        │   ├── hupe1.wav
        │   └── hupe2.wav        <- mehrere Töne: wird bei jedem Spiel
        │                           zufällig einer davon abgespielt
        └── ... (weitere Begriffe)
```

**Regeln, die das Programm automatisch beachtet:**

- Jeder **Kategorie-Ordner** (z. B. `Tiere`) wird automatisch im
  Dropdown-Menü oben im Spiel angezeigt.
- Jeder **Unterordner** darin (z. B. `Kuh`) ist ein "Begriff" und
  braucht **mindestens ein Bild** (`.png`, `.jpg`, `.jpeg`, `.gif`,
  `.bmp`, `.webp`). Ohne Bild wird der Ordner ignoriert.
- Ton ist **optional**, aber empfohlen (`.wav`, `.mp3`, `.ogg`,
  `.flac`, `.m4a`, `.aac`).
- Gibt es **mehrere Audiodateien** in einem Begriffs-Ordner, wählt das
  Spiel bei jedem Aufdecken automatisch **zufällig eine davon** aus
  (genau wie gewünscht).
- Gibt es mehrere Bilddateien in einem Ordner, wird ebenfalls
  zufällig eines davon verwendet.

Sie müssen an Ihrer bestehenden Ordnerstruktur **nichts ändern** –
legen Sie den `logoData`-Ordner einfach direkt neben `memory_game.py`.

## Installation & Start

```bash
pip install -r requirements.txt
python memory_game.py
```

Beim ersten Start:
- Wird `logoData` direkt neben `memory_game.py` gefunden, startet das
  Spiel sofort.
- Andernfalls öffnet sich ein Auswahlfenster, in dem Sie einmalig den
  Ordner `logoData` (egal wo er liegt) auswählen können. Der Pfad wird
  in `data_dir_config.txt` gespeichert, sodass Sie ihn nicht erneut
  auswählen müssen.

## Bedienung

1. Oben im Fenster über das **Dropdown "Kategorie"** eine Kategorie
   wählen (z. B. "Tiere", "Menschen", "Verkehrsmitteln").
2. Über das Dropdown **"Anzahl Bilder"** wählen, wie viele Karten
   angezeigt werden sollen: 6, 8, 10 oder 12 (= 3 bis 6 Paare). Hat
   eine Kategorie nicht genug Begriffe für die gewünschte Anzahl,
   spielt das Spiel automatisch mit weniger Paaren und zeigt einen
   Hinweis dazu an.
3. Das Spielfeld mit den verdeckten Karten erscheint automatisch.
3. Kind klickt zwei Karten an – Bild + Ton werden angezeigt/abgespielt.
4. Passen sie zusammen, bleiben sie sichtbar (grün markiert).
5. Passen sie nicht zusammen, drehen sie sich nach kurzer Zeit wieder um.
6. **"🔄 Neu starten (neue Bilder)"** wählt automatisch drei **neue,
   zufällige** Begriffe aus der aktuell gewählten Kategorie – bei
   mehreren Audiodateien pro Begriff auch wieder zufällig ausgewählt.
7. Wechselt man die Kategorie im Dropdown, startet automatisch ein
   neues Spiel mit Begriffen aus der neuen Kategorie.
8. **"🔁 Nochmal hören"** ist aktiv, sobald genau eine Karte aufgedeckt
   ist (man wartet also noch auf die zweite Wahl). Damit kann sich das
   Kind den Ton beliebig oft erneut anhören, **ohne dass dies als
   zusätzlicher Versuch gezählt wird** – die Versuche bleiben korrekt.
9. Im Feld **"Name des Kindes"** kann vor dem Spiel der Name
   eingetragen werden (optional – bleibt das Feld leer, wird
   "Unbekannt" gespeichert).

## Ergebnisse speichern (CSV)

Sobald ein Spiel **vollständig gelöst** ist (alle Paare gefunden),
wird automatisch eine Zeile in `ergebnisse.csv` (im Projektordner)
gespeichert, mit folgenden Spalten:

| Spalte | Bedeutung |
|---|---|
| Datum, Uhrzeit | Zeitpunkt des Spielendes |
| Name | eingetragener Name des Kindes (oder "Unbekannt") |
| Kategorie | gespielte Kategorie |
| Kartenanzahl | Anzahl der Karten (6/8/10/12) |
| Gefundene_Paare | Anzahl gefundener Paare |
| Versuche | Anzahl Versuche (zwei aufgedeckte Karten = 1 Versuch) |
| Dauer_Sekunden | Zeit vom Spielstart bis zum Sieg |

Die Datei kann direkt in Excel oder LibreOffice Calc geöffnet werden
(Spaltentrennzeichen: Semikolon `;`, Kodierung: UTF-8 mit BOM, damit
Umlaute korrekt angezeigt werden). Jedes abgeschlossene Spiel fügt
eine neue Zeile hinzu – so lässt sich der Fortschritt eines Kindes
über mehrere Sitzungen hinweg verfolgen.

### Ergebnisse direkt im Programm ansehen (ohne Excel)

Über den Knopf **"📊 Ergebnisse anzeigen"** öffnet sich ein eigenes
Fenster mit einer Tabelle aller gespeicherten Ergebnisse (neueste
zuerst) - ganz ohne Excel oder Office nötig:

- **Spalten anklicken** sortiert die Tabelle nach dieser Spalte
  (nochmal klicken kehrt die Reihenfolge um).
- **"🔄 Aktualisieren"** lädt die Tabelle neu, z. B. wenn gerade ein
  weiteres Spiel abgeschlossen wurde.
- Ist noch keine Datei vorhanden, erscheint ein entsprechender
  Hinweis statt einer leeren Tabelle.

## Fehlerbehebung: Es werden Buchstaben statt Bilder angezeigt

Das bedeutet, dass Pillow (PIL) ein Bild nicht laden konnte. Führen Sie
im aktivierten venv aus:

```bash
python diagnose.py
```

Das Skript zeigt genau, ob Pillow korrekt installiert ist und ob alle
Bilddateien in `logoData/` gültig sind (inkl. genauer Fehlermeldung
pro Datei, falls etwas nicht stimmt). Häufigste Ursache: eine zur
Python-Version nicht passende Pillow-Installation - siehe
`requirements.txt` (bei Python 3.7 wird `Pillow<10.0.0` benötigt).

## Hinweise

- Falls eine Kategorie weniger als drei gültige Begriffe (Bild
  vorhanden) enthält, spielt das Spiel automatisch mit weniger Paaren
  und zeigt einen Hinweis dazu an.
- Falls `pygame` nicht installiert ist, läuft das Spiel weiterhin,
  nur ohne Ton.
- Bilder werden automatisch quadratisch zugeschnitten und skaliert,
  Sie müssen sie nicht vorher bearbeiten.

## Mögliche Erweiterungen (Ideen)

- Sprachausgabe des Begriffs beim Aufdecken (z. B. mit `pyttsx3`)
- Schwierigkeitsstufen (z. B. 4 statt 3 Paare für ältere Kinder –
  dazu einfach `PAIRS_COUNT` in `memory_game.py` anpassen)
- Statistik über mehrere Sitzungen hinweg
- Belohnungs-Animation nach jedem gefundenen Paar

## Projektstruktur

```
logopaedie_memory/
├── memory_game.py         # Hauptprogramm (starten!)
├── requirements.txt
├── README.md
├── data_dir_config.txt    # wird automatisch erzeugt (Pfad zu logoData)
└── logoData/               # Ihre eigenen Bild-/Ton-Ordner (siehe oben)
```
