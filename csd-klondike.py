#!/usr/bin/env python3
"""
Klondike Solitaire (draw 1 or draw 3) with animated cards, built on pyglet 2.x.

Install:   pip install pyglet          (Windows: py -m pip install pyglet)
Run:       python csd-klondike.py [--refresh] [resource-folder]
           (Windows: py csd-klondike.py ...)
Options:   --refresh   rebuild the image cache (see below) even if it exists
           -h, --help  show a short usage message and exit

Resources
    All pictures and sounds live in one "resource folder". Inside it there is
    one folder for every set of card faces, named cards_1, cards_2, cards_3,
    ... (as many as you like), and a folder for the sounds:
        resources/
            cards_1/    one complete set of card faces
            cards_2/    another set of card faces (optional)
            cards_3/    ...
            card-backs/ the card backs (shared by all the sets)
            sounds/     the sound effects
    The game looks for the resource folder in these places (first match wins):
    the path given on the command line, then a folder named "resources" next
    to this script, then one named "resources" in the current folder.

Card face sets (resources/cards_1, cards_2, ...)
    The sets are used in numeric order (cards_2 before cards_10). The
    "Card Faces" button (or the F key) switches to the next set, and after
    the last one starts again at cards_1. The chosen set is remembered.
    Each card is a file named rank + suit letter, e.g. "AS.png", "2D.png",
    "10H.png", "KC.png". The rank is A, 2-10, J, Q or K (T also means 10) and
    the suit letter is S (spades), H (hearts), C (clubs) or D (diamonds);
    upper or lower case both work. Names that do not fit this pattern exactly
    are not used (a warning lists them when the cache is built).
    A set folder may also hold "empty.png" (the empty-pile marker). A set
    without one uses the empty.png of the first set that has one.

Table background (resources/background.png)
    If the resource folder holds a file named \"background.png\", it is used
    as the picture behind the cards instead of the plain green colour. It is
    scaled to cover the whole window (keeping its proportions, so a little of
    the edge may be cut off) and follows the window when it is resized. With
    no such file, or if it cannot be read, the green colour is used.

Card backs (resources/card-backs)
    Any number of card backs, named "back_1.png", "back_2.png", "back_3.png",
    ... The backs are used in numeric order (back_2 before back_10); the Card
    Back button (or the B key) steps through them and then starts again at
    back_1. The chosen back is remembered. The same backs are used with every
    set of card faces. If there are none, a plain drawn back is used.
    If images are missing, those cards are drawn with plain shapes instead.
    Only the set you were last using is loaded when the game starts. Another
    set is read the first time you switch to it (a "Loading card faces..."
    message is shown for a moment). Nothing is loaded in the background while
    you play, so the game never pauses by itself.
    The first launch decodes the images and saves the raw pixels, one file per
    set ("cards_1.cache", "cards_2.cache", ...) plus one for the card backs
    ("card-backs.cache"), in the folder
    ~/.config/csd-klondike (on Windows: %LOCALAPPDATA%\\csd-klondike),
    creating the folder if needed; later launches load those files, which is
    much faster. The background picture is not cached: it is read
    from the resource folder every time (keep it a moderate size, since a
    large PNG is slow to decode, especially without the Pillow library).
    The window appears at once with a \"Loading...\" message that
    names what is being loaded (images, sounds), so a slow start never looks
    as if nothing is happening.
    A set's cache is rebuilt automatically if its images change
    (including adding or removing a card back), and the files are safe to
    delete. Start the game with --refresh to rebuild all of them anyway.

Sounds (resources/sounds)
    These files are used (.mp3, .wav, .ogg or .flac):
        card_placement  a card lands on a pile        flip          a card turns over
        illegal         a move is not allowed         refill_stock  waste goes back to stock
        applause        you won                       lose_game     "Check Moves" finds none left
    Sounds that are missing or cannot be decoded are simply skipped. The short
    effects are decoded when the game starts; the two long clips (applause and
    lose_game) are streamed while they play, so they cost nothing until used.
    Note that on Linux pyglet may need FFmpeg installed to play MP3 files; on
    Windows pyglet uses the built-in Media Foundation decoder, which handles MP3.

Statistics and settings
    The top bar shows your wins, losses, win percentage and fastest win.
    A game counts as a WIN when all 52 cards reach the foundations. It counts
    as a LOSS when
      - you start a new game (New Game, N, or switching draw mode) after making
        at least one move without having won, or
      - you close the window while no useful move is left (even if you never
        pressed Check Moves). Closing a game that still has moves is not counted.
    Drawing from the stock counts as a move; turning the waste back over into
    the stock does not.
    The fastest win is the shortest time from the first move to the last
    card reaching a foundation, shown as minutes:seconds.
    "Reset Stats" (click it twice to confirm) clears wins, losses and the
    fastest win.
    The fastest win is measured from the player's FIRST MOVE (not from the
    end of the deal): the clock stays at 0:00 until the first card is moved
    or the first draw is made from the stock.
    The program also remembers, between runs: the window size and position,
    the card faces, the card back, the draw mode (1 or 3) and the
    statistics. They are kept in
    "settings.json" in the same folder as the cache file. A missing or damaged
    settings file is ignored and the defaults are used.

Platforms
    The program runs on Linux and Windows. All file locations are built with
    os.path, so they work with / or \\ separators. Per-system differences:
    the cache folder (see above) and, as just described, MP3 decoding.

Controls
    Mouse       drag cards / card runs between piles, click the stock to draw
    Dbl-click   send a card to a foundation (right-click works too)
    Shift+Ctrl  CHEAT: while both are held, any card or run of cards may be
                dropped on an empty tableau column (not only a king)
    N           new game            U or Ctrl+Z   undo
    A           auto-move cards to the foundations
    C           check whether any moves are left (the Check Moves button)
    1 / 3       switch to draw-1 / draw-3 (starts a new game)
    B           switch between the available card backs
    M           mute / unmute sound
    Esc         quit
The window can be resized freely; everything scales with it.

--------------------------------------------------------------------------
HOW THE PROGRAM IS ORGANISED (read this first)
--------------------------------------------------------------------------
The most important idea is that the game keeps TWO separate things:

  1. LOGICAL STATE - which card is in which pile.  The piles are plain Python
     lists of Card objects:
         Solitaire.stock            face-down draw pile (last item = top)
         Solitaire.waste            cards turned over from the stock
         Solitaire.found[0..3]      the four foundation piles (A -> K)
         Solitaire.tab[0..6]        the seven tableau columns (last = bottom-most,
                                    i.e. the card you can play)
     Game rules (can_drop, do_move, ...) only look at and change these lists.

  2. VISUAL STATE - where each card is currently drawn on screen (card.x,
     card.y) plus a little tween (animation) that slides it toward a target.

The two are connected by ONE function, Solitaire.relayout():
     - targets() looks at the logical piles and computes where every card
       SHOULD be on screen (a dict: card -> (x, y)),
     - relayout() tells every card to slide there (Card.move_to).
So to make something happen the code just (a) changes the piles and (b) calls
relayout().  Dealing, drawing from the stock, moving cards, undo and "snap
back after a bad drop" are all animated by that same mechanism.

Source layout (top to bottom):
     constants & helpers
     Assets ............ loads the pictures from ONE folder (a card set, or the backs)
     CardSets .......... all the card sets and the card backs, and what is selected
     Sounds ............ loads the sound effects from resources/sounds and plays them
     *Drawable classes . draw one card face / back / slot, either from an image
                         (ImageDrawable) or with plain shapes (Shape*)
     Card .............. one playing card: position, animation, flip, drawing
     Button, Slot ...... small UI pieces
     Solitaire ......... the window: layout, rules, mouse/keyboard, main loop

pyglet's coordinate system has (0, 0) at the BOTTOM-left of the window and y
grows upward, so "lower on the screen" means a smaller y.

GLOSSARY
    stock       the face-down draw pile (top-left)
    waste       where cards drawn from the stock are turned face up
    foundation  the four piles (top-right) built up from Ace to King, by suit
    tableau     the seven columns you play on
    run         several face-up cards in a column that are moved together
    slot        the marker drawn where a pile is (visible when the pile is empty)
    tween       an animation that slides a value from A to B over a short time
    snap        jump to a position instantly, with no animation
    ref         a pile reference such as ("tab", 3); see Solitaire.pile_of()

FOLLOWING ONE MOVE THROUGH THE CODE
    1. on_mouse_press    finds the card under the pointer (hit_test), starts a drag
    2. on_mouse_drag     moves the dragged cards along with the pointer
    3. on_mouse_release  works out which pile it was dropped on; can_drop()
                         applies the Klondike rules
    4. do_move           changes the pile lists, turns over the uncovered card,
                         saves an undo snapshot
    5. relayout          gives every card a new target position, so cards slide
    6. Card.update       runs 60 times a second and advances each slide
    7. on_draw           draws every visible card at its current position
    8. update            afterwards starts the win celebration if all cards are up
                         (the "no more moves" test only runs when you press Check Moves)

PYTHON IDIOMS USED (in case some look unfamiliar)
    lst[-1]            the LAST item of a list (the top card of a pile)
    lst[-3:]           the last three items;  lst[:-1] is all but the last
    lst[:]             a COPY of the whole list
    a, b = x, y        assigns two variables at once ("tuple unpacking")
    {k: v for ...}     a "dict comprehension": builds a dictionary in one line
    x if cond else y   a one-line if/else that produces a value
    lambda p=p: ...    a tiny anonymous function; "p=p" freezes the current value
    yield              turns a function into a generator that hands back items
                       one at a time
    @property          lets a method be read like a variable (self.locked)
    @staticmethod      a method that does not use `self`
    f"...{x}..."       an f-string: {x} is replaced by the value of x
    _name              a leading underscore marks something as internal
"""
import argparse
import hashlib
import io
import json
import math
import os
import random
import re
import struct
import sys
import tempfile
import time
import zlib

import pyglet
from pyglet import shapes
from pyglet import image as pyimage
from pyglet import sprite as pysprite
from pyglet import media as pymedia
from pyglet import display as pydisplay
from pyglet.window import key, mouse

# --------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------
START_W, START_H = 1000, 720    # window size the first time the game runs
MIN_W, MIN_H = 880, 560         # the window cannot be resized smaller than this
BAR = 80                        # height of the top bar: two rows (buttons, then status)
ROW1_DROP = 40                  # row 1 (buttons): its bottom edge is this far below the window top
ROW2_DROP = 72                  # row 2 (status line and Reset Stats), measured the same way
# Card size tuning: smaller numbers = bigger cards (columns then squeeze
# together sooner when they get long).
WIDTH_FIT = 8.6                 # card width  ~ window width  / WIDTH_FIT
HEIGHT_FIT = 4.5                # card height ~ window height / HEIGHT_FIT
ASPECT = 242 / 340              # card width / height of the supplied images
FLIP_DUR = 0.22                 # seconds a card takes to flip over

# Fonts are only used for the shape fallback (no images). pyglet uses the
# first family in the list that exists on the machine.
FONT = ("Arial", "DejaVu Sans", "Segoe UI Symbol", "Helvetica")
# Suits are numbered 0..3 in this order (spade, heart, club, diamond).
# Hearts and diamonds (1 and 3) are the red suits.
SUITS = "\u2660\u2665\u2663\u2666"
RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]

SLOT_FILL = (16, 92, 52)        # colours of empty-pile markers (shape fallback)
SLOT_EDGE = (70, 140, 100)
IMG_EXTS = (".png", ".jpg", ".jpeg", ".gif", ".bmp")
# Names of the resource folder and the two folders inside it.
RESOURCE_DIR = "resources"
SOUNDS_SUBDIR = "sounds"
BACKS_SUBDIR = "card-backs"          # the card backs live here, shared by every set
BACKGROUND_NAME = "background.png"   # optional table picture, in the resource folder
# Card face sets live in folders named cards_1, cards_2, ... (any number).
CARDS_DIR_PATTERN = re.compile(r"cards_(\d+)", re.IGNORECASE)
# How card file names are translated into ranks and suits when loading images.
# A card file is named rank + ONE suit letter, in either case:
#     AS  2D  10H  KC  JS  ...
# rank: A, 2-9, 10, J, Q or K ("T" is also accepted for 10)
# suit: S = spades, H = hearts, C = clubs, D = diamonds
# The pattern is matched against the WHOLE file name (without its extension),
# so a name like "KDE" or "A_S" is not mistaken for a card.
CARD_NAME = re.compile(r"(10|[A2-9TJQK])([SHCD])", re.IGNORECASE)
# Rank character -> rank number ("10" is handled separately).
RANK_KEYS = {"A": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8,
             "9": 9, "T": 10, "J": 11, "Q": 12, "K": 13}
# Suit letter -> suit number (the same numbering as SUITS above).
SUIT_KEYS = {"S": 0, "H": 1, "C": 2, "D": 3}

# Sound settings.
SND_EXTS = (".mp3", ".wav", ".ogg", ".flac")
# How loud each effect is (0.0 - 1.0). Change these to taste; a name that is
# not listed plays at full volume.
SOUND_VOLUME = {"card_placement": 0.8, "flip": 0.7, "illegal": 0.6,
                "refill_stock": 0.8, "applause": 0.7, "lose_game": 0.7}
# These two clips are long, so they are not decoded in advance (that can take
# seconds). They are STREAMED: pyglet decodes them a little at a time, in its
# audio thread, while they play, so starting one never makes the game pause.
LONG_SOUNDS = ("applause", "lose_game")

# Counter used to decide which moving card is drawn on top (see next_z).
_z = 0


def next_z():
    """Monotonic counter used to order moving cards (later = drawn on top).

    Every time a card starts moving (or is picked up) it takes the next
    number as its `z`. on_draw draws moving cards in increasing z order, so
    the card that moved most recently appears in front of the others."""
    # `global` is needed because we change the module-level counter.
    global _z
    _z += 1
    return float(_z)


def say(message):
    """Print an informational message without ever raising an error.

    A plain say() can fail on Windows: a console that uses an old code page
    cannot show every character (for example a non-English user name inside a
    file path), and say() then raises UnicodeEncodeError. These messages
    are only hints for the player, so a failure to show one is ignored."""
    try:
        print(message)
    except Exception:
        try:
            # Second try: replace anything the console cannot show with "?".
            print(message.encode("ascii", "replace").decode("ascii"))
        except Exception:
            pass


def overlap(ax, ay, aw, ah, bx, by, bw, bh):
    """Area of the intersection of two rectangles (x, y, width, height).
    Returns 0 when they do not overlap. Used to decide which pile a dragged
    card was dropped on."""
    w = min(ax + aw, bx + bw) - max(ax, bx)
    h = min(ay + ah, by + bh) - max(ay, by)
    return w * h if (w > 0 and h > 0) else 0


def make_label(text, weight="normal", **kw):
    """Create a pyglet Label. Pass weight="bold" for bold text.

    A Label is pyglet's text object: it is created once, positioned with
    .x / .y, and drawn with .draw(). `**kw` passes every other option
    (font size, colour, anchors, ...) straight through to pyglet.

    Current pyglet Labels take a `weight` argument and have no `bold`
    attribute, so `weight` is what we pass. Only the older pyglet 2.0 Label
    wants a `bold` flag instead; that spelling is tried only if pyglet rejects
    `weight` (Python raises TypeError for an argument a function does not
    have), so the rest of the program only ever says weight="bold"."""
    if weight == "normal":
        return pyglet.text.Label(text, **kw)        # the default: nothing to add
    try:
        return pyglet.text.Label(text, weight=weight, **kw)
    except TypeError:
        return pyglet.text.Label(text, bold=(weight == "bold"), **kw)


# --------------------------------------------------------------------------
# Image assets (from the resources/cards folder)
# --------------------------------------------------------------------------
def _natural_key(text):
    """Sort key that compares the digits inside a name as NUMBERS, so that
    "2" sorts before "10" (plain alphabetical order would put "10" first).
    "back_1", "back_2", ... "back_10" therefore come out in the right order.

    re.split("(\\d+)", "a10b") gives ["a", "10", "b"]: text and digit strings
    alternate, so the two kinds are always compared with their own kind."""
    return [int(part) if part.isdigit() else part
            for part in re.split(r"(\d+)", text)]


def parse_name(fname):
    """Map a file name to ('card', (rank, suit)), ('back', style),
    ('empty', None) or None (not one of ours).

    Card files are rank + suit letter: "AS.png", "2D.png", "10H.png"."""
    # splitext("AS.png") -> ("AS", ".png"): the name and the extension.
    stem, ext = os.path.splitext(fname)
    if ext.lower() not in IMG_EXTS:              # also skips "*.png.bad"
        return None
    low = stem.lower()
    # Special images: "back_3" -> back number "3" (any number of backs is
    # allowed), "empty" -> the empty-pile marker.
    if low.startswith("back"):
        return "back", (low[4:].strip("_- ") or "default")
    if low.startswith("empty"):
        return "empty", None
    # Otherwise it must be a card. fullmatch() demands that the WHOLE name
    # fits the pattern, and returns None if it does not.
    match = CARD_NAME.fullmatch(stem)
    if match is None:
        return None
    rank_text = match.group(1).upper()           # "10", "A", "K", ...
    suit_letter = match.group(2).upper()         # "S", "H", "C" or "D"
    rank = 10 if rank_text == "10" else RANK_KEYS[rank_text]
    return "card", (rank, SUIT_KEYS[suit_letter])


def _entries(folder, exts):
    """Return a list of (file name, file bytes) for every file directly
    inside `folder` whose extension is in `exts`, in alphabetical order.
    Sub-folders are not searched.

    Each file is opened, read and closed straight away, so nothing stays open
    afterwards. (A file that is still open can stop Windows from replacing or
    deleting it while the game is running.)"""
    found = []
    # os.listdir gives the names of everything in the folder; sorted() makes
    # the order the same on every system.
    for name in sorted(os.listdir(folder)):
        path = os.path.join(folder, name)
        # Skip sub-folders and files of other kinds (e.g. "A.png.bad").
        if os.path.isfile(path) and os.path.splitext(name)[1].lower() in exts:
            with open(path, "rb") as fh:
                found.append((name, fh.read()))
    return found


def _with_temp_file(data, ext, loader):
    """Write `data` to a temporary file and return loader(path).

    Some decoders can only read real files, not data held in memory (this
    can happen with the audio and image decoders on Windows). The temporary
    file is deleted again afterwards, even if loading fails."""
    fd, path = tempfile.mkstemp(suffix=ext)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        return loader(path)
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


def _load_image(data, ext):
    """Decode image bytes with pyglet; falls back to a temp file if the
    decoder cannot read from memory."""
    try:
        # pyglet picks the decoder from the file extension, so give it a
        # simple ASCII name with the right extension.
        return pyimage.load("img" + ext, file=io.BytesIO(data))
    except Exception:
        return _with_temp_file(data, ext, pyimage.load)


def _load_sound(data, ext, streaming=False):
    """Open sound bytes with pyglet.

    streaming=False decodes the whole clip into memory straight away (fine
    for a short effect). streaming=True only opens it; the audio is then
    decoded a little at a time while it plays (right for a long clip, and a
    streamed clip can only be played once, so open it again for each play).

    If the decoder cannot do that from memory, fall back to decoding the
    whole clip, from a temporary file if even that is needed."""
    try:
        return pymedia.load("sound" + ext, file=io.BytesIO(data),
                            streaming=streaming)
    except Exception:
        pass
    if streaming:                       # streaming from memory did not work
        try:
            return pymedia.load("sound" + ext, file=io.BytesIO(data),
                                streaming=False)
        except Exception:
            pass
    return _with_temp_file(
        data, ext, lambda path: pymedia.load(path, streaming=False))


def find_resource_dir(arg=None):
    """Find the resource folder (the one that holds "cards_1", "cards_2", ...,
    "card-backs" and "sounds").

    Looked for in this order, first match wins: the path given on the command
    line (`arg`), a folder named "resources" next to this script, a folder
    named "resources" in the current folder. Returns None if there is none."""
    here = os.path.dirname(os.path.abspath(__file__))
    # Build the list of places to look, best choice first ("cands" =
    # candidates); the first one that really is a folder wins.
    cands = []
    if arg:
        cands.append(arg)
        if not os.path.isdir(arg):
            say(f"warning: resource folder '{arg}' not found; "
                f"looking for '{RESOURCE_DIR}' instead.")
    for base in (here, os.getcwd()):
        cands.append(os.path.join(base, RESOURCE_DIR))
    for c in cands:
        if os.path.isdir(c):
            return c
    return None


def resource_subdir(resource_dir, name):
    """The folder `name` (e.g. "sounds") inside the resource folder, or None
    if there is no resource folder or it has no such folder."""
    if not resource_dir:
        return None
    path = os.path.join(resource_dir, name)
    return path if os.path.isdir(path) else None


def find_card_sets(resource_dir):
    """The card face sets in the resource folder, as a list of
    (name, folder path) in numeric order: one entry for every sub-folder
    named cards_<number>. The name is the number as text, e.g. "2".
    Returns an empty list if there are none."""
    if not resource_dir:
        return []
    try:
        entries = os.listdir(resource_dir)
    except OSError:
        return []
    found = []
    for entry in entries:
        path = os.path.join(resource_dir, entry)
        # fullmatch: the whole folder name must be "cards_" + digits.
        match = CARDS_DIR_PATTERN.fullmatch(entry)
        if match and os.path.isdir(path):
            found.append((match.group(1), path))
    # Numeric order, so cards_2 comes before cards_10.
    found.sort(key=lambda item: _natural_key(item[0]))
    if not found and os.path.isdir(os.path.join(resource_dir, "cards")):
        say("note: found a 'cards' folder but no 'cards_1', 'cards_2', ... "
            "folders. Rename 'cards' to 'cards_1' to use it.")
    return found


def _scan_set(folder):
    """Cheaply look inside one card set folder WITHOUT decoding any picture.
    Returns (True if it has empty.png, True if it contains card backs). The
    second answer is only used to point out backs left in the old place."""
    has_empty = has_backs = False
    try:
        names = os.listdir(folder)
    except OSError:
        return False, False
    for name in names:
        info = parse_name(name)
        if info and info[0] == "empty":
            has_empty = True
        elif info and info[0] == "back":
            has_backs = True
    return has_empty, has_backs


def _scan_backs(folder):
    """The names of the card backs in the card-backs folder, in numeric order
    (["1", "2", ..., "10"]), found from the file names alone."""
    if not folder:
        return []
    try:
        names = os.listdir(folder)
    except OSError:
        return []
    found = set()
    for name in names:
        info = parse_name(name)
        if info and info[0] == "back":
            found.add(info[1])
    return sorted(found, key=_natural_key)


# --- decoded-image cache ---------------------------------------------------
# Decoding 54 PNG files is the slowest part of starting up (especially with
# pyglet's built-in pure-Python PNG decoder). So after the first run we store
# the decoded pixels in one file (one per card set) and read that instead.
# File layout:
#     8-byte magic | 4-byte header length | JSON header | compressed pixel blobs
# The header holds a "signature" of the image source: a hash of the CONTENTS
# of the image files. The cache is therefore ignored and rebuilt whenever the
# images change, and reused whenever they are the same - no matter where the
# files are, what the program was started from, or what their timestamps say.
# The file lives in the user's config folder rather than next to the program.
# The cache file and the settings file both live in a folder with this name
# (see _cache_dir below for where that folder is).
APP_DIR_NAME = "csd-klondike"
SETTINGS_NAME = "settings.json"
CACHE_MAGIC = b"KCACHE1\n"


def _cache_dir():
    """The folder that holds the cache file.

    Linux (and anything else): ~/.config/csd-klondike
    Windows: %LOCALAPPDATA%\\csd-klondike, the usual place for per-user cache data
    (if that variable is missing, its normal location under the home folder).
    os.path.expanduser("~") is the user's home folder on every system."""
    home = os.path.expanduser("~")
    if sys.platform.startswith("win"):
        base = os.environ.get("LOCALAPPDATA") or os.path.join(home, "AppData", "Local")
        return os.path.join(base, APP_DIR_NAME)
    return os.path.join(home, ".config", APP_DIR_NAME)


def _cache_path(stem="cards_1"):
    """Full path of a cache file: <stem>.cache, e.g. cards_2.cache for the
    second card set or card-backs.cache for the card backs."""
    return os.path.join(_cache_dir(), f"{stem}.cache")


# --- saved settings ------------------------------------------------------------
# The window size/position, card back, draw mode and win/loss counts are kept
# in a small JSON text file in the same folder as the cache file.
def _settings_path():
    return os.path.join(_cache_dir(), SETTINGS_NAME)


def read_settings():
    """Load the saved settings as a dict. A missing, unreadable or damaged
    file simply gives an empty dict, so the defaults are used."""
    try:
        with open(_settings_path(), "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def write_settings(data):
    """Save the settings dict. Written to a temporary file first and then
    swapped in, so an interrupted write cannot leave a half-written file."""
    os.makedirs(_cache_dir(), exist_ok=True)
    path = _settings_path()
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, path)


def _clamp_int(value, lo, hi, default):
    """`value` limited to the range lo..hi, or `default` if it is not a whole
    number at all (the settings file could contain anything)."""
    # bool is a kind of int in Python (True == 1), so reject it explicitly.
    if isinstance(value, bool) or not isinstance(value, int):
        return default
    return max(lo, min(hi, value))


def _valid_time(value):
    """A saved time as a float number of seconds, or None if the settings
    file holds anything that is not a sensible time."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    # `value != value` is only true for NaN ("not a number").
    if value != value or not (0 <= value <= 10 ** 7):
        return None
    return float(value)


def _mm_ss(seconds):
    """Format a number of seconds as minutes:seconds, e.g. 272.9 -> "4:32".
    (`//` is whole-number division and `%` the remainder; :02d pads the
    seconds to two digits.)"""
    secs = int(seconds)
    return f"{secs // 60}:{secs % 60:02d}"


def _screens():
    """The list of monitors (empty if pyglet cannot tell us)."""
    try:
        return list(pydisplay.get_display().get_screens())
    except Exception:
        return []


def _source_signature(folder, kinds):
    """A fingerprint of the images a cache holds, used to tell if it is stale.

    `kinds` says which images count: ("card", "empty") for a card set,
    ("back",) for the card backs. Files of other kinds in the same folder do
    not matter, so they cannot make the cache look out of date.

    It is a SHA-1 hash of the image data itself, so it only changes when the
    pictures change: not when files are moved or copied, and not when their
    timestamps change. (Earlier versions used the path and modified time,
    which can differ from one run to the next for harmless reasons, making
    the cache look out of date every time.) Hashing a few hundred KB takes
    only a few milliseconds.

    The leading "v4" is a format number: it lets us change how the
    fingerprint is made in the future (old caches then simply rebuild)."""
    h = hashlib.sha1()
    # Hash every wanted image together with its file name, in a fixed order.
    # Including the name means that renaming a card, or adding or removing a
    # card back, also counts as a change.
    for name, data in _entries(folder, IMG_EXTS):
        info = parse_name(name)
        if info and info[0] in kinds:
            h.update(name.encode("utf-8", "surrogateescape"))
            h.update(data)
    return ["v4", h.hexdigest()]


def _write_cache(path, sig, items):
    """Save decoded images. `items` is a list of (kind, val, w, h, rgba)."""
    # The header is plain JSON describing every image; the compressed pixel
    # data ("blobs") follows it in the file, in the same order.
    header = {"sig": sig, "items": []}
    blobs = []
    for kind, val, w, h, raw in items:
        blob = zlib.compress(raw, 1)                # level 1 = fast to write
        header["items"].append([kind, val, w, h, len(blob)])
        blobs.append(blob)
    head = json.dumps(header).encode("utf-8")
    # Make ~/.config/csd-klondike if it does not exist yet (exist_ok: no error if
    # it already does).
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"                             # write, then swap in, so a
    with open(tmp, "wb") as f:                      # crash never leaves a
        f.write(CACHE_MAGIC)                        # half-written cache
        # struct.pack("<I", n) stores n as a 4-byte little-endian integer, so
        # the reader knows how many bytes of JSON header to expect.
        f.write(struct.pack("<I", len(head)))
        f.write(head)
        for blob in blobs:
            f.write(blob)
    os.replace(tmp, path)                           # atomic rename into place


def _read_cache(path, sig):
    """Load decoded images, or return None if the cache is missing, damaged
    or was made from different images."""
    with open(path, "rb") as f:
        data = f.read()                             # the whole file as bytes
    if not data.startswith(CACHE_MAGIC):            # not one of our files
        return None
    pos = len(CACHE_MAGIC)                          # `pos` = read position
    # Read back the 4-byte header length written by _write_cache.
    (n,) = struct.unpack_from("<I", data, pos)
    pos += 4
    header = json.loads(data[pos:pos + n].decode("utf-8"))
    pos += n
    if header["sig"] != sig:                        # images changed: stale
        return None
    items = []
    for kind, val, w, h, size in header["items"]:
        # Each image's compressed pixels follow one after another.
        raw = zlib.decompress(data[pos:pos + size])
        pos += size
        if len(raw) != w * h * 4:                   # damaged file
            return None
        if kind == "card":
            val = tuple(val)                        # JSON turned it into a list
        items.append((kind, val, w, h, raw))
    return items


def find_background(resource_dir):
    """Path of background.png in the resource folder (any capitalisation of
    the name), or None if there is none."""
    if not resource_dir:
        return None
    try:
        for name in os.listdir(resource_dir):
            if name.lower() == BACKGROUND_NAME:
                path = os.path.join(resource_dir, name)
                if os.path.isfile(path):
                    return path
    except Exception:
        pass
    return None


def load_background(path):
    """Load the table picture straight from its file (it is not cached) and
    return it as an image, or None if it cannot be read."""
    try:
        return pyimage.load(path)
    except Exception as e:
        say(f"warning: could not load the background picture: {e}")
        return None


class Assets:
    """The pictures from ONE folder: either a card set (the card faces and
    the empty-pile marker, e.g. resources/cards_1) or the card backs
    (resources/card-backs). `kinds` says which kind of image to read. It must
    be created AFTER the window exists (textures need an OpenGL context).
    Which set is shown, and which back, is decided by CardSets."""

    def __init__(self, source, refresh=False, cache_stem="cards_1", quiet=False,
                 kinds=("card", "empty")):
        # `refresh` (the --refresh option) skips reading the cache, so the
        # images are decoded again and the cache file is rebuilt.
        # `cache_stem` ("cards_2", "card-backs", ...) names this folder's cache
        # file; `kinds` is ("card", "empty") for a set and ("back",) for backs.
        self.faces = {}                 # (rank, suit) -> texture
        self.backs = {}                 # back number (as text) -> texture
        self.empty = None               # texture for empty piles
        self.empty_color = (100, 70, 66)   # fill colour of that texture
        if not source:
            if not quiet:
                say("No card images found (looked for "
                    f"{RESOURCE_DIR}/cards_1, cards_2, ...); "
                    "drawing cards with shapes.")
            return
        label = os.path.basename(os.path.normpath(source))  # e.g. "cards_2"
        cache_path = _cache_path(cache_stem)

        # `items` will become a list of (kind, val, width, height, pixels) for
        # every image; `sig` fingerprints the source to validate the cache.
        # Fast path: reuse the pixels decoded on an earlier run. With
        # --refresh we deliberately do not look at the existing cache.
        # `reason` records why the cache is NOT being used, so that we can
        # tell the player whenever the (slow) rebuild happens.
        items, sig = None, None
        reason = "no cache file yet"
        if refresh:
            reason = "--refresh"
        try:
            sig = _source_signature(source, kinds)
            if not refresh and os.path.exists(cache_path):
                items = _read_cache(cache_path, sig)
                if items is None:
                    reason = "the images changed or the cache file is not valid"
        except Exception as e:
            items = None                            # any problem: just decode
            reason = f"the cache could not be read: {e}"
        # Slow path: decode the image files, then save the cache for next time.
        if items is None:
            if refresh:
                say(f"Rebuilding the card image cache for {label} (--refresh).")
            else:
                say(f"Building the card image cache for {label} ({reason}).")
            items = self._decode_all(source, kinds)
            if items and sig is not None:
                try:
                    _write_cache(cache_path, sig, items)
                    say(f"Card image cache written to {cache_path}")
                except Exception as e:
                    # The game still works without a cache, but say so: a
                    # cache that silently fails to save means a slow start
                    # on every launch with no hint as to why.
                    say(f"warning: could not write the cache: {e}")

        # Turn the pixel data into GPU textures (needs the OpenGL context).
        # "RGBA" = 4 bytes per pixel (red, green, blue, alpha/transparency),
        # so one row of the image is w * 4 bytes (the "pitch").
        for kind, val, w, h, raw in items:
            tex = pyimage.ImageData(w, h, "RGBA", raw, pitch=w * 4).get_texture()
            if kind == "card":
                self.faces[val] = tex       # val = (rank, suit)
            elif kind == "back":
                self.backs[val] = tex       # val = back number, e.g. "3"  (card-backs folder)
            else:                           # the empty-pile picture
                self.empty = tex
                # Sample the centre pixel of the empty-pile image; the
                # "stock is empty" ring uses it as its inner colour.
                # (row h//2 is the middle row; each pixel is 4 bytes wide.)
                i = ((h // 2) * w + w // 2) * 4
                self.empty_color = (raw[i], raw[i + 1], raw[i + 2])
        missing = 52 - len(self.faces)          # how many faces we did not find
        if missing and "card" in kinds:         # (not a complaint about the backs folder)
            say(f"warning: {missing} card image(s) missing in {label}; "
                "those cards are drawn with shapes.")

    @staticmethod
    def _decode_all(source, kinds):
        """Decode every wanted image file. Returns a list of
        (kind, val, width, height, rgba_bytes). Files of a kind that this
        folder is not used for (e.g. a back_1.png inside a card set) are
        skipped without comment."""
        try:
            entries = _entries(source, IMG_EXTS)
        except Exception as e:                      # missing folder, permissions, ...
            say(f"Could not read card images from {source}: {e}")
            return []
        items = []
        unknown = []                                # image files we could not identify
        for fname, data in entries:
            info = parse_name(fname)
            if not info:                            # not one of our images
                unknown.append(fname)
                continue
            kind, val = info                        # e.g. ("card", (10, 1))
            if kind not in kinds:                   # right name, wrong folder
                continue
            try:
                img = _load_image(data, os.path.splitext(fname)[1].lower())
                d = img.get_image_data()
                # Positive pitch keeps pyglet's native (bottom-up) row order,
                # which is also how the cache is read back in.
                raw = bytes(d.get_data("RGBA", d.width * 4))
                items.append((kind, val, d.width, d.height, raw))
            except Exception as e:
                say(f"warning: could not load {fname}: {e}")
        if unknown:
            # Most likely a file with an old-style or misspelt name: say so,
            # because the card would otherwise just be drawn with shapes.
            shown = ", ".join(unknown[:6]) + (", ..." if len(unknown) > 6 else "")
            say(f"warning: ignored {len(unknown)} image file(s) in "
                f"{os.path.basename(os.path.normpath(source))} whose names are "
                f"not recognised ({shown}). Card files are named like AS.png, "
                "2D.png, 10H.png; card backs back_1.png, back_2.png, ...")
        return items


class CardSets:
    """Every card set (cards_1, cards_2, ...), the card backs, and which of
    them are selected.

    It looks like a single set of pictures to the rest of the program:
    `faces`, `empty`, `current_back()` and so on describe the SELECTED set and
    the selected back. Behind that:

      - Card faces: sets are loaded lazily. Only the selected set is read at
        start-up; any other set is read the first time it is selected. (There
        is deliberately no loading in the background: it would make the game
        pause at some random moment.)
      - empty.png comes from the selected set when it has one; otherwise from
        the first other set that does. (A cheap look at the file names,
        _scan_set, tells us which one without loading it.)
      - Card backs come from ONE folder (resources/card-backs) and are the
        same whichever set of faces is selected. The selected back is
        remembered by NAME ("3")."""

    def __init__(self, sets, backs_dir=None, refresh=False):
        # `sets` is a list of (name, folder) as made by find_card_sets();
        # `backs_dir` is the card-backs folder (or None).
        self.names = [name for name, _ in sets]             # ["1", "2", ...]
        self._paths = dict(sets)                            # name -> folder
        # For each set: (has empty.png, contains backs). No decoding needed.
        self._scan = {name: _scan_set(path) for name, path in sets}
        self._refresh = refresh
        self._loaded = {}               # name -> Assets, filled in as needed
        self._none = Assets(None, quiet=True)   # stands in when there are no sets
        self.index = 0                  # position of the selected set in names
        self.back_name = None           # the selected back, e.g. "3"
        self._backs_dir = backs_dir
        self._back_names = _scan_backs(backs_dir)   # e.g. ["1", "2", "10"]
        self._backs = None              # the backs' Assets, loaded on first use
        if not sets:
            say("No card images found (looked for "
                f"{RESOURCE_DIR}/cards_1, cards_2, ...); "
                "drawing cards with shapes.")
        if not self._back_names:
            say(f"No card backs found (looked for {RESOURCE_DIR}/{BACKS_SUBDIR}); "
                "drawing the card backs with shapes.")
            # Backs left in the old place (inside a card set) are no longer
            # used: point that out, because it is an easy thing to miss.
            stray = [f"cards_{n}" for n in self.names if self._scan[n][1]]
            if stray:
                say(f"note: card backs found in {', '.join(stray)} are not used "
                    f"any more; move them to {RESOURCE_DIR}/{BACKS_SUBDIR}.")
        if refresh:                     # --refresh: rebuild every cache now
            for name in self.names:
                self._get(name)
            if self._backs_dir:
                self._get_backs()

    # -- loading -----------------------------------------------------------
    def _get(self, name):
        """The Assets of set `name`, loading it first if necessary."""
        if name not in self._loaded:
            self._loaded[name] = Assets(self._paths[name], self._refresh,
                                        f"cards_{name}")
        return self._loaded[name]

    def _get_backs(self):
        """The Assets holding the card backs, loading them first if necessary."""
        if self._backs is None:
            self._backs = Assets(self._backs_dir, self._refresh, "card-backs",
                                 kinds=("back",))
        return self._backs

    def is_loaded(self, name):
        """True if set `name` has already been read (selecting it is instant)."""
        return name in self._loaded

    def next_name(self):
        """The name of the set that cycle_faces() would select, or None if
        there is only one set."""
        if len(self.names) < 2:
            return None
        return self.names[(self.index + 1) % len(self.names)]

    # -- which set is selected ------------------------------------------------
    @property
    def current(self):
        """The Assets of the selected set."""
        return self._get(self.names[self.index]) if self.names else self._none

    def current_name(self):
        return self.names[self.index] if self.names else None

    def cycle_faces(self):
        """Select the next set (wrapping round). False if there is only one."""
        if len(self.names) < 2:
            return False
        self.index = (self.index + 1) % len(self.names)
        return True

    def select_set(self, name):
        """Select a set by name (used to restore the saved choice)."""
        if name in self.names:
            self.index = self.names.index(name)
            return True
        return False

    @property
    def faces(self):
        return self.current.faces

    # -- the empty-pile marker (with fall-back to other sets) ---------------------
    def _empty_owner(self):
        """The name of the set that provides empty.png: the selected set if it
        has one, else the first other set that does (None if no set has one)."""
        if not self.names:
            return None
        current = self.names[self.index]
        for name in [current] + [n for n in self.names if n != current]:
            if self._scan[name][0]:
                return name
        return None

    @property
    def empty(self):
        owner = self._empty_owner()
        return self._get(owner).empty if owner else None

    @property
    def empty_color(self):
        owner = self._empty_owner()
        return self._get(owner).empty_color if owner else self._none.empty_color

    # -- the card backs ---------------------------------------------------------------
    @property
    def back_names(self):
        """The available card backs, in numeric order, e.g. ["1", "2", "10"]."""
        return self._back_names

    @property
    def max_backs(self):
        """How many card backs there are (to decide about the button)."""
        return len(self._back_names)

    def current_back_name(self):
        """Name of the selected back, or None if there are no backs. If the
        remembered name does not exist, the first back is used."""
        names = self._back_names
        if not names:
            return None
        return self.back_name if self.back_name in names else names[0]

    def current_back(self):
        """Texture of the selected back, or None (a drawn back is then used)."""
        name = self.current_back_name()
        if name is None:
            return None
        return self._get_backs().backs.get(name)

    def cycle_back(self):
        """Select the next back (wrapping round). False if there is only one."""
        names = self._back_names
        if len(names) < 2:
            return False
        self.back_name = names[(names.index(self.current_back_name()) + 1) % len(names)]
        return True

    def select_back(self, name):
        """Select a back by name (used to restore the saved choice). Returns
        False if there is no back with that name."""
        if name in self._back_names:
            self.back_name = name
            return True
        return False


# --------------------------------------------------------------------------
# Sound effects (from the resources/sounds folder)
# --------------------------------------------------------------------------
class Sounds:
    """Loads the sound files and plays them by name, e.g. play("flip").

    The sound files are read from the given folder (normally
    resources/sounds). A file's name (without extension) is the name of the
    sound. Every problem is handled quietly, so the game still works without
    sound."""

    def __init__(self, source, tick=None):
        # `tick` (optional) is called after each clip is decoded, so the
        # caller can keep the window repainted during this slow step.
        # Two dictionaries because loading is done in two stages: first the
        # raw file bytes are read (`raw`), then a short effect is decoded
        # into playable audio (`clips`) and moved from one dictionary to the
        # other. The long clips stay in `raw` and are streamed when played.
        self.raw = {}               # name -> (extension, file bytes), not decoded
        self.clips = {}             # name -> decoded pyglet source (None = failed)
        self._failed = set()        # long clips that could not be opened (warn once)
        self.enabled = True         # False while muted
        self.players = []           # short effects that are currently playing
        self.long_player = None     # the one applause / lose_game clip playing
        if not source:
            say(f"No sound files found (looked for {RESOURCE_DIR}/{SOUNDS_SUBDIR}); "
                "playing without sound.")
            return
        try:
            entries = _entries(source, SND_EXTS)
        except Exception as e:                      # missing folder, permissions, ...
            say(f"Could not read sounds from {source}: {e}")
            return
        # Keep the bytes of every sound file (cheap; no decoding yet).
        for fname, data in entries:
            stem, ext = os.path.splitext(fname)     # ("flip", ".mp3")
            # The lower-cased stem is the sound's name: "flip.mp3" is played
            # with play("flip").
            self.raw[stem.lower()] = (ext.lower(), data)
        # Decode the short effects now; the long clips are streamed later.
        # (`list(self.raw)` is a copy of the names, because _decode removes
        # entries from the dictionary while we loop.)
        for name in list(self.raw):
            if name not in LONG_SOUNDS:
                self._decode(name)
                if tick:
                    tick()
        # Start up the audio system now, while the window is still hidden.
        # Otherwise this happens when the first sound is played, in the middle
        # of the opening deal, and on some systems it takes a noticeable moment.
        try:
            pymedia.get_audio_driver()
        except Exception:
            pass                            # no such function / no audio device

    @property
    def available(self):
        """True if at least one sound could be played."""
        return bool(self.raw) or any(self.clips.values())

    def _decode(self, name):
        """Decode one clip if that has not happened yet; returns the clip
        (a pyglet Source) or None if it is missing or cannot be decoded."""
        if name in self.clips:              # already decoded (or known to fail)
            return self.clips[name]
        # pop() removes the entry and returns it; None if there was none.
        item = self.raw.pop(name, None)
        if item is None:                    # no such sound file
            return None
        ext, data = item
        try:
            # The whole clip is decoded into memory once (streaming=False),
            # so every later play() starts instantly.
            self.clips[name] = _load_sound(data, ext)
        except Exception as e:
            self.clips[name] = None             # remember: do not retry
            say(f"warning: could not decode sound '{name}': {e} "
                "(on Linux, MP3 files may need FFmpeg installed)")
        return self.clips[name]

    def _stream(self, name):
        """Open a long clip for streaming. Every play needs a NEW source,
        because a streamed source can only be played once. Returns None (and
        warns once) if the clip is missing or cannot be opened."""
        item = self.raw.get(name)
        if item is None or name in self._failed:
            return None
        ext, data = item
        try:
            return _load_sound(data, ext, streaming=True)
        except Exception as e:
            self._failed.add(name)
            say(f"warning: could not open sound '{name}': {e} "
                "(on Linux, MP3 files may need FFmpeg installed)")
            return None

    def play(self, name, volume=1.0, long=False):
        """Play a sound once. Several sounds can overlap. A `long` sound
        (applause / game over) replaces the previous long one."""
        if not self.enabled:                # muted
            return
        if name in LONG_SOUNDS and name in self.raw:
            clip = self._stream(name)       # a fresh streaming source each time
        else:
            clip = self._decode(name)       # a short effect: already decoded
        if clip is None:                    # missing or undecodable: stay silent
            return
        if long:
            self.stop_long()                # only one long clip at a time
        try:
            player = pymedia.Player()               # one Player per playback
            player.queue(clip)
            player.volume = volume * SOUND_VOLUME.get(name, 1.0)
            player.play()
        except Exception:
            return                                  # e.g. no audio device
        # Keep a reference to every playing Player. The long one gets its own
        # slot so it can be stopped on its own (e.g. when a new game starts).
        if long:
            self.long_player = player
        else:
            self.players.append(player)

    @staticmethod
    def _release(player):
        """Stop a player and free its audio resources."""
        try:
            player.pause()
            player.delete()
        except Exception:
            pass

    def stop_long(self):
        """Stop the applause / game-over clip if one is playing."""
        if self.long_player is not None:
            self._release(self.long_player)
            self.long_player = None

    def stop_all(self):
        """Stop every sound (used when the player mutes)."""
        self.stop_long()
        for p in self.players:
            self._release(p)
        self.players = []

    def update(self):
        """Called every frame: free the players whose sound has finished."""
        if not self.players:
            return
        alive = []                          # players that are still playing
        for p in self.players:
            if p.playing:
                alive.append(p)
            else:                           # finished: free its resources
                self._release(p)
        while len(alive) > 32:                      # safety cap
            self._release(alive.pop(0))
        self.players = alive


# --------------------------------------------------------------------------
# Drawables: same small interface for images and for the shape fallback
#   resize(cw, ch)   place(x, y, scale)   draw(full)
#
#   resize - called whenever the card size changes (window resize)
#   place  - move to (x, y); `scale` < 1 squeezes the width, which is how the
#            flip animation is done (1.0 = normal width)
#   draw   - draw it; `full` is False while squeezed (skips the small text)
# --------------------------------------------------------------------------
class ImageDrawable:
    """Draws a card face/back/slot from a texture using a pyglet Sprite.

    A texture is the picture stored on the graphics card; a Sprite is a
    movable, scalable rectangle that displays a texture. The image file is
    never resized: the Sprite simply stretches the picture to the current
    card size whenever the window changes size."""

    def __init__(self, tex):
        # One Sprite per drawable; its position and scale are set in place()
        # and resize() below.
        self.sprite = pysprite.Sprite(tex)
        self.tw, self.th = tex.width, tex.height    # size of the source image
        self.cw = self.ch = 1                       # size on screen
        self.sx = self.sy = 1.0                     # image -> screen scale

    def set_texture(self, tex):
        """Swap the picture (used to change the card back)."""
        self.sprite.image = tex
        self.tw, self.th = tex.width, tex.height
        self.resize(self.cw, self.ch)

    def resize(self, cw, ch):
        self.cw, self.ch = cw, ch
        # Scale factors that stretch the image to exactly cw x ch pixels.
        self.sx = cw / self.tw
        self.sy = ch / self.th
        self.sprite.scale_y = self.sy

    def place(self, x, y, scale):
        # Shrink the width by `scale` but keep the card centred on its slot,
        # so a flipping card appears to turn around its middle.
        w = self.cw * scale
        self.sprite.scale_x = self.sx * scale
        self.sprite.x = x + (self.cw - w) / 2
        self.sprite.y = y

    def draw(self, full=True):
        # `full` only matters to the shape fallback (it hides the text while
        # a card is squeezed mid-flip); a picture needs no special case.
        self.sprite.draw()


class ShapeFace:
    """Fallback card face: white rectangle + rank/suit text (no images).

    Only used for a card whose picture could not be loaded. It has the same
    methods as ImageDrawable (resize / place / draw), so Card does not need
    to know which kind it is using."""

    def __init__(self, rank, suit):
        # Red ink for hearts/diamonds (suits 1 and 3), near-black otherwise.
        ink = (200, 25, 35, 255) if suit in (1, 3) else (25, 25, 30, 255)
        # e.g. rank 10, suit 1 -> "10" + heart symbol.  (Ranks start at 1 but
        # list indexes start at 0, hence the `rank - 1`.)
        text = f"{RANKS[rank - 1]}{SUITS[suit]}"
        self.cw = self.ch = 10              # real size is set later by resize()
        self.rect = shapes.BorderedRectangle(
            0, 0, 10, 10, border=2, color=(252, 252, 248),
            border_color=(70, 70, 70))
        # Rank+suit in the top-left and bottom-right corners, big suit symbol
        # in the middle.
        self.tl = make_label(text, weight="bold", font_name=FONT, font_size=14,
                             color=ink, anchor_x="left", anchor_y="top")
        self.br = make_label(text, weight="bold", font_name=FONT, font_size=14,
                             color=ink, anchor_x="right", anchor_y="bottom")
        self.c = make_label(SUITS[suit], font_name=FONT, font_size=38,
                            color=ink, anchor_x="center", anchor_y="center")

    def resize(self, cw, ch):
        self.cw, self.ch = cw, ch
        self.rect.height = ch
        # Text sizes are proportional to the card height.
        self.tl.font_size = self.br.font_size = max(8, ch * 0.125)
        self.c.font_size = max(12, ch * 0.34)

    def place(self, x, y, scale):
        # Same centred squeeze as ImageDrawable.place: width * scale, then
        # shift right by half of what was lost so the middle stays put.
        w = self.cw * scale
        self.rect.x, self.rect.y, self.rect.width = x + (self.cw - w) / 2, y, w
        if scale >= 0.999:          # text only matters when not mid-flip
            m = self.cw * 0.075     # margin from the card edge
            self.tl.x, self.tl.y = x + m, y + self.ch - m * 0.5
            self.br.x, self.br.y = x + self.cw - m, y + m * 0.5
            self.c.x, self.c.y = x + self.cw / 2, y + self.ch / 2

    def draw(self, full=True):
        self.rect.draw()                    # white card body first
        if full:                            # then the text on top of it
            self.tl.draw()
            self.br.draw()
            self.c.draw()


class ShapeBack:
    """Fallback card back: white border with a blue panel inside."""

    def __init__(self):
        self.cw = self.ch = 10
        self.outer = shapes.BorderedRectangle(
            0, 0, 10, 10, border=2, color=(245, 245, 245),
            border_color=(70, 70, 70))
        self.inner = shapes.BorderedRectangle(
            0, 0, 10, 10, border=2, color=(40, 95, 175),
            border_color=(20, 60, 130))

    def set_texture(self, tex):
        pass                        # nothing to swap for the drawn back

    def resize(self, cw, ch):
        self.cw, self.ch = cw, ch
        self.outer.height = ch
        m = cw * 0.075
        self.inner.height = ch - 2 * m

    def place(self, x, y, scale):
        w = self.cw * scale                 # squeezed width (flip animation)
        m = self.cw * 0.075                 # border between outer and inner panel
        self.outer.x, self.outer.y = x + (self.cw - w) / 2, y
        self.outer.width = w
        iw = max(2, (self.cw - 2 * m) * scale)
        self.inner.x, self.inner.y = x + (self.cw - iw) / 2, y + m
        self.inner.width = iw

    def draw(self, full=True):
        self.outer.draw()
        self.inner.draw()


class ShapeSlot:
    """Fallback marker for an empty pile: a dark green outlined rectangle."""

    def __init__(self):
        self.cw = self.ch = 10
        self.rect = shapes.BorderedRectangle(
            0, 0, 10, 10, border=2, color=SLOT_FILL, border_color=SLOT_EDGE)

    def resize(self, cw, ch):
        self.cw, self.ch = cw, ch
        self.rect.width, self.rect.height = cw, ch

    def place(self, x, y, scale=1.0):
        self.rect.x, self.rect.y = x, y

    def draw(self, full=True):
        self.rect.draw()


# --------------------------------------------------------------------------
# Card: drawing + tween animation
# --------------------------------------------------------------------------
class Card:
    """One playing card.

    A Card knows its rank/suit, whether it is face up, where it is drawn
    (x, y) and how it is currently animating. It does NOT know which pile it
    is in - that is tracked by the pile lists in Solitaire.

    Animation model: move_to() sets a target and remembers the start point;
    update() advances a timer every frame and interpolates x, y from start to
    target using an ease-out curve.
    """

    def __init__(self, rank, suit, assets):
        self.rank = rank            # 1 (ace) .. 13 (king)
        self.suit = suit            # 0..3, see SUITS
        self.red = suit in (1, 3)   # True for hearts and diamonds
        self.face_up = False        # logical state (the flip animation follows)

        # --- position / tween state ---
        # A "tween" slides x, y from (sx, sy) to (tx, ty). `t` counts up from 0
        # and progress is (t - delay) / dur, which runs from 0.0 to 1.0.
        self.x = self.y = 0.0                       # where it is drawn now
        self.sx = self.sy = self.tx = self.ty = 0.0  # tween start / target
        self.t = self.dur = self.delay = 0.0        # elapsed, length, start delay
        self.animating = False      # True while sliding (or waiting to start)
        self.dragging = False       # True while the mouse is holding it
        self.launched = False       # used by the win celebration
        self.vx = self.vy = 0.0     # velocity, win celebration only
        self.z = 0.0                # drawing order among moving cards
        self.flip_t = None          # None, or seconds into the flip animation
        self.pending_flip = False   # flip face-up when the slide finishes
        # Sound hooks. `on_sound(name)` is set by the game; `land_sound` is
        # the sound to play when this card finishes its current slide.
        self.on_sound = None
        self.land_sound = None
        # Remember the last placement of the face / back drawable so we only
        # touch the sprite when something changed (saves work every frame).
        self._kf = self._kb = None

        # Use the image if we have one, otherwise the drawn fallback.
        # (dict.get returns None instead of raising an error when the key is
        # missing, which is how "no image for this card" is detected.)
        ftex = assets.faces.get((rank, suit))
        self.face = ImageDrawable(ftex) if ftex else ShapeFace(rank, suit)
        btex = assets.current_back()
        self.back = ImageDrawable(btex) if btex else ShapeBack()
        self._size = None           # on-screen size, set by resize()

    # -- sizing ------------------------------------------------------------
    def resize(self, cw, ch):
        """Tell both sides of the card the new on-screen size (the window
        was resized)."""
        self._size = (cw, ch)
        self.face.resize(cw, ch)
        self.back.resize(cw, ch)
        self._kf = self._kb = None          # force a re-place on next draw

    def set_face_texture(self, tex):
        """Use a different face picture (another card set). `tex` is None if
        the new set has no picture for this card: it is then drawn with shapes."""
        if tex is None:
            if not isinstance(self.face, ShapeFace):
                self.face = ShapeFace(self.rank, self.suit)
        elif isinstance(self.face, ImageDrawable):
            self.face.set_texture(tex)              # same kind: just swap the picture
        else:
            self.face = ImageDrawable(tex)          # was drawn with shapes before
        if self._size:                              # a new drawable needs its size
            self.face.resize(*self._size)
        self._kf = None                             # force a re-place on next draw

    def set_back_texture(self, tex):
        """Swap in a different card-back picture (the Card Back button, or
        another card set). `tex` is None if there is no back picture."""
        if tex is None:
            if not isinstance(self.back, ShapeBack):
                self.back = ShapeBack()
        elif isinstance(self.back, ImageDrawable):
            self.back.set_texture(tex)
        else:
            self.back = ImageDrawable(tex)
        if self._size:
            self.back.resize(*self._size)
        self._kb = None

    # -- state changes -----------------------------------------------------
    def set_face(self, up):
        """Turn the card face up/down. The logical state changes at once;
        flip_t starts the visual flip animation."""
        if self.face_up == up:
            return
        self.face_up = up
        self.flip_t = 0.0
        if self.on_sound:
            self.on_sound("flip")           # the game decides whether to play it

    def move_to(self, tx, ty, dur=None, delay=0.0, z=None):
        """Start sliding toward (tx, ty).

        dur   seconds the slide takes (default: depends on the distance)
        delay seconds to wait before starting (used to stagger the deal)
        z     drawing order; by default it becomes the newest, so moving
              cards are drawn above everything else
        """
        if self.dragging:                   # the mouse is in control
            return
        # relayout() calls move_to for EVERY card after every change; most
        # cards already have this target, and this early exit makes that free.
        if tx == self.tx and ty == self.ty:
            return                          # already there / already heading there
        # Start from wherever the card is right now (even mid-slide).
        self.sx, self.sy = self.x, self.y
        self.tx, self.ty = tx, ty
        self.t = 0.0
        self.delay = delay
        dist = math.hypot(tx - self.x, ty - self.y)
        # Longer trips take a bit longer, clamped to 0.16 - 0.45 seconds.
        self.dur = dur if dur else max(0.16, min(0.45, 0.12 + dist / 2600.0))
        self.animating = True
        # Take the newest z unless the caller supplied one, so that a card
        # that just started moving is drawn in front of the others.
        self.z = z if z is not None else next_z()

    def snap(self, x, y):
        """Jump to (x, y) immediately, cancelling any animation."""
        self.x = self.tx = self.sx = x
        self.y = self.ty = self.sy = y
        self.animating = False
        self.land_sound = None              # a cancelled slide makes no sound

    # -- per-frame ---------------------------------------------------------
    def update(self, dt):
        """Advance the animations by dt seconds (called every frame)."""
        if self.animating:
            self.t += dt
            if self.t >= self.delay:                # past the start delay?
                p = (self.t - self.delay) / self.dur     # progress 0..1
                if p >= 1.0:                        # arrived
                    self.x, self.y = self.tx, self.ty
                    self.animating = False
                    if self.land_sound and self.on_sound:
                        self.on_sound(self.land_sound)   # "thump" on landing
                    self.land_sound = None
                    if self.pending_flip:           # e.g. dealt top card
                        self.pending_flip = False
                        self.set_face(True)
                else:
                    # Ease-out: fast at first, slowing toward the end. Plain
                    # `p` would move at constant speed; this curve feels
                    # smoother and more natural.
                    e = 1.0 - (1.0 - p) ** 3          # ease-out cubic
                    # Linear interpolation: start + (distance) * fraction.
                    self.x = self.sx + (self.tx - self.sx) * e
                    self.y = self.sy + (self.ty - self.sy) * e
        if self.flip_t is not None:
            self.flip_t += dt
            if self.flip_t >= FLIP_DUR:
                self.flip_t = None                  # flip finished

    def draw(self):
        """Draw the card at its current position, mid-flip if it is flipping.

        `scale` is the width factor: 1.0 normally, shrinking to nearly 0 and
        growing back during a flip, which looks like the card turning."""
        scale = 1.0                                 # 1.0 = full width
        face_up = self.face_up
        if self.flip_t is not None:                 # horizontal flip effect
            # First half of the flip: the OLD side shrinks to a sliver.
            # Second half: the NEW side grows back to full width.
            # p runs 0 -> 1. abs(1 - 2p) goes 1 -> 0 -> 1, i.e. full width,
            # edge-on at the halfway point, full width again. The 0.08 floor
            # keeps the card from vanishing completely.
            p = min(1.0, self.flip_t / FLIP_DUR)
            scale = max(0.08, abs(1.0 - 2.0 * p))
            face_up = self.face_up if p >= 0.5 else (not self.face_up)
        # `k` describes the placement: whole-pixel x, y and the flip scale.
        # Whole pixels keep the artwork sharp, and the cache (_kf / _kb)
        # means the sprite is only touched when `k` actually changes.
        k = (round(self.x), round(self.y), round(scale, 3))
        # `*k` unpacks the tuple into the three arguments x, y, scale.
        if face_up:
            if k != self._kf:                       # only re-place if changed
                self.face.place(*k)
                self._kf = k
            self.face.draw(scale >= 0.999)
        else:
            if k != self._kb:
                self.back.place(*k)
                self._kb = k
            self.back.draw()


# --------------------------------------------------------------------------
# Button and pile slot
# --------------------------------------------------------------------------
class Button:
    """A clickable rectangle with a text label in the top bar."""

    def __init__(self, text, x, y, w, h, callback, drop=0, right=None):
        # A button is a rectangle (x, y = bottom-left corner, w x h = size)
        # with centred text. Functions are ordinary values in Python, so the
        # `callback` can simply be stored and called later: callback().
        self.x, self.y, self.w, self.h = x, y, w, h
        self.callback = callback            # function called when clicked
        # Where the button sits when the window is resized: `drop` is how far
        # its bottom edge is below the top of the window, and `right` (if
        # given) keeps it that many pixels from the right edge.
        self.drop = drop
        self.right = right
        self.rect = shapes.BorderedRectangle(
            x, y, w, h, border=2, color=(28, 122, 78),
            border_color=(150, 214, 172))
        self.label = make_label(text, weight="bold", font_size=12,
                                x=x + w / 2, y=y + h / 2,
                                anchor_x="center", anchor_y="center",
                                color=(255, 255, 255, 255))

    def set_text(self, text):
        """Change the text shown on the button."""
        self.label.text = text

    def set_y(self, y):
        """Move vertically (the top bar follows the top of the window)."""
        self.y = y
        self.rect.y = y
        self.label.y = y + self.h / 2

    def set_x(self, x):
        """Move horizontally (used by buttons anchored to the right edge)."""
        self.x = x
        self.rect.x = x
        self.label.x = x + self.w / 2

    def contains(self, px, py):
        """True if the point (px, py) is inside the button."""
        return self.x <= px <= self.x + self.w and self.y <= py <= self.y + self.h

    def draw(self):
        # Rectangle first, then the text on top of it.
        self.rect.draw()
        self.label.draw()


class Slot:
    """An empty-pile marker (uses empty.png when available).

    One Slot exists for every place a pile can be (stock, waste, 4
    foundations, 7 columns). Slots are drawn underneath the cards, so one is
    only visible where a pile has no cards."""

    def __init__(self, kind, idx, assets, letter=None):
        self.kind, self.idx = kind, idx     # e.g. ("tab", 3) = tableau column 3
        self.img = ImageDrawable(assets.empty) if assets.empty else ShapeSlot()
        self.label = None
        if letter:                          # faint "A" / "K" hint on the slot
            self.label = make_label(letter, font_size=30, anchor_x="center",
                                    anchor_y="center", color=(255, 255, 255, 110))

    def set_texture(self, tex):
        """Use a different empty-pile picture (another card set). `tex` is
        None if there is none: a plain outlined rectangle is drawn instead.
        (Call layout() afterwards to size and place the new picture.)"""
        if tex is None:
            if not isinstance(self.img, ShapeSlot):
                self.img = ShapeSlot()
        elif isinstance(self.img, ImageDrawable):
            self.img.set_texture(tex)
        else:
            self.img = ImageDrawable(tex)

    def layout(self, x, y, cw, ch):
        """Place and size the marker (called on every window resize)."""
        self.img.resize(cw, ch)
        self.img.place(x, y, 1.0)
        if self.label:
            self.label.font_size = max(10, ch * 0.27)
            self.label.x, self.label.y = x + cw / 2, y + ch / 2

    def draw(self):
        self.img.draw()                     # the marker picture / rectangle
        if self.label:
            self.label.draw()               # then the faint A / K hint


# --------------------------------------------------------------------------
# The game / window
# --------------------------------------------------------------------------
class Solitaire(pyglet.window.Window):
    """The game window. It owns the piles, applies the rules, handles mouse
    and keyboard input, and draws everything."""

    def __init__(self, card_sets=None, sound_source=None, refresh_cache=False,
                 backs_dir=None, background=None):
        # Read the settings saved by the previous run (an empty dict the first
        # time). They are needed now because the window size is chosen when
        # the window is created.
        saved = read_settings()
        win = saved.get("window")
        win = win if isinstance(win, dict) else {}
        # Never open bigger than the biggest monitor, or smaller than allowed.
        screens = _screens()
        max_w = max([s.width for s in screens] or [10 ** 5])
        max_h = max([s.height for s in screens] or [10 ** 5])
        width = _clamp_int(win.get("width"), MIN_W, max_w, START_W)
        height = _clamp_int(win.get("height"), MIN_H, max_h, START_H)
        # Create the actual OS window (images and sounds need it). It starts
        # hidden (visible=False) so that it can be moved to its saved position
        # before it appears, instead of flashing up in the wrong place first.
        super().__init__(width=width, height=height,
                         caption="Klondike Solitaire", resizable=True,
                         visible=False)
        self.set_minimum_size(MIN_W, MIN_H)
        # Loading the pictures and (especially) decoding the sounds can take
        # many seconds, during which nothing could be drawn. So the window is
        # shown NOW with a "Loading..." message, before any slow work starts;
        # it is repainted while the sounds load and replaced by the game when
        # the first frame is drawn.
        self._loading_label = None
        self._show_loading(win)
        self.settings = saved               # kept so unknown keys survive a save
        self._warned_settings = False       # only warn once if saving fails
        # Window position bookkeeping (see _check_position and on_move).
        self._wanted_pos = None             # saved position we are trying to restore
        self._pos_attempts = 0              # how many times we have checked it
        self._last_pos = None               # latest position reported by on_move
        # Load the pictures; every card then picks its own from here.
        # `card_sets` is the list of (name, folder) from find_card_sets() and
        # `backs_dir` the card-backs folder. Only the selected set is read
        # now; the other sets load later (see CardSets).
        self._bg_path = background          # optional table picture (or None)
        self.assets = CardSets(card_sets or [], backs_dir, refresh_cache)
        # Restore the card faces and the card back.
        self.assets.select_set(saved.get("card_faces"))
        self.assets.select_back(saved.get("card_back"))
        # All 52 cards, created once and reused for every game.
        self.cards = [Card(r, s, self.assets)
                      for s in range(4) for r in range(1, 14)]
        # Load the sound effects. Cards never play sounds themselves; they
        # call `on_sound`, which we point at our own _card_sound method.
        self.sounds = Sounds(sound_source, tick=self._loading_tick)
        for c in self.cards:                # cards report their sounds to us
            c.on_sound = self._card_sound
        # 1 or 3 cards per stock click; restored from the settings if valid.
        dc = saved.get("draw_count")
        self.draw_count = dc if (type(dc) is int and dc in (1, 3)) else 3
        # Win / loss statistics (restored too). `game_active` is True while a
        # game has been started but not yet won or abandoned (see new_game).
        self.wins = _clamp_int(saved.get("wins"), 0, 10 ** 9, 0)
        self.losses = _clamp_int(saved.get("losses"), 0, 10 ** 9, 0)
        # Fastest win, in seconds (None until the first win).
        self.best_time = _valid_time(saved.get("best_time"))
        self.game_active = False
        # --- the logical state: piles of cards (see the module docstring) ---
        self.stock, self.waste = [], []
        self.found = [[] for _ in range(4)]
        self.tab = [[] for _ in range(7)]
        self.waste_fan = 0                  # how many waste cards are fanned out
        self.undo_stack = []                # snapshots taken before each move
        self.drag = None                    # info about the drag in progress
        self.last_click = None              # (card, time) for double-click
        # Game phase flags; while any is set the board ignores mouse input.
        self.dealing = self.auto = self.won = self.win_pending = False
        self.timer_on = False               # is the clock running?
        self.moves = 0                      # shown in the top bar
        self.elapsed = 0.0                  # seconds played
        # Win celebration: cards still to launch, how many are launched, time.
        self.win_queue, self.win_idx, self.win_time = [], 0, 0.0
        self.silent_flips = False           # True while cards flip in bulk
        self.stuck = False                  # True while "no more moves" is shown
        self.notice_time = 0.0              # seconds left to show the short notice
        self.reset_armed = 0.0              # seconds left to confirm "Reset Stats"
        self._faces_switch_pending = False  # a Card Faces switch is waiting to run
        self._laid_out_size = None          # window size the layout was last made for

        # Order matters: work out sizes, create the visuals, then position them.
        self._compute_layout()
        self._build_ui()
        self.apply_layout()
        # pyglet calls on_resize while the window is being created; this
        # flag tells on_resize to wait until everything above exists.
        self._ready = True
        # Call self.update 60 times per second (this drives ALL animation).
        pyglet.clock.schedule_interval(self.update, 1 / 60.0)
        self.new_game()                     # shuffle and start the first deal
        # Put the window where it was last time (if that spot is still on a
        # monitor), then show it.
        x, y = win.get("x"), win.get("y")
        # (bool is a kind of int in Python, so exclude it explicitly.)
        if (isinstance(x, int) and isinstance(y, int)
                and not isinstance(x, bool) and not isinstance(y, bool)
                and self._position_ok(x, y)):
            self._wanted_pos = (x, y)
            # Windows and macOS honour a position set before the window is
            # shown, so there is no flash in the wrong place there...
            self.set_location(x, y)
        self.set_visible(True)
        if self._wanted_pos:
            # ...but many Linux window managers ignore a position set before
            # the window appears (or place it a title-bar's height off). So
            # look again a moment after the window is on screen.
            pyglet.clock.schedule_once(self._check_position, 0.2)

    def _show_loading(self, win):
        """Show the window at once with a "Loading..." message.

        The window is normally kept hidden until the game is ready, which
        could leave the player looking at nothing for many seconds. Here it is
        moved to its saved position (if it has one) and shown early, and the
        message is drawn directly and put on screen. Any failure is ignored:
        the game then simply starts the old way."""
        try:
            x, y = win.get("x"), win.get("y")
            have_pos = (isinstance(x, int) and isinstance(y, int)
                        and not isinstance(x, bool) and not isinstance(y, bool)
                        and self._position_ok(x, y))
            if have_pos:
                self.set_location(x, y)
            self.set_visible(True)
            self.dispatch_events()          # let the window really appear
            if have_pos:
                # Some window managers (GNOME, for one) ignore the position
                # asked for before the window appears and centre it instead.
                # Move it to the right place NOW, before anything is drawn in
                # it, so the player never sees the game jump from the middle
                # of the screen to its saved spot.
                self._place_window(x, y)
            self._loading_label = make_label(
                "Loading...", weight="bold", font_size=28,
                x=self.width // 2, y=self.height // 2,
                anchor_x="center", anchor_y="center",
                color=(255, 255, 255, 255))
            self._loading_tick()
        except Exception:
            self._loading_label = None

    def _pump_events(self, seconds):
        """Let the window system work for a short while (handles its events)
        without drawing anything. Window moves are carried out
        asynchronously, so after asking for one we have to wait a moment."""
        end = time.perf_counter() + seconds
        while time.perf_counter() < end:
            self.dispatch_events()
            time.sleep(0.01)

    def _place_window(self, x, y):
        """Get the freshly shown window to (x, y) before the first drawing.

        Looks where the window is; if it is not at (x, y), moves it there,
        and if it ends up a little off (typically by the height of the title
        bar) moves it once more by the difference. Gives up quietly after
        that (the later check in _check_position still reports a problem).
        Takes no time at all when the window is already in the right place."""
        self._pump_events(0.05)
        for attempt in range(2):
            cx, cy = self.get_location()
            dx, dy = x - cx, y - cy
            if abs(dx) <= 2 and abs(dy) <= 2:
                return
            if attempt == 0:
                self.set_location(x, y)
            elif abs(dx) <= 100 and abs(dy) <= 100:
                self.set_location(x + dx, y + dy)   # frame / title-bar offset
            else:
                return                      # did not move at all: leave it
            self._pump_events(0.15)

    def _loading_tick(self):
        """Redraw the loading screen and let the window system handle its
        events. Called between the slow start-up steps so that the window
        stays painted and is not reported as "not responding"."""
        if self._loading_label is None:
            return
        try:
            self.dispatch_events()
            self.switch_to()
            pyglet.gl.glClearColor(12 / 255, 102 / 255, 58 / 255, 1)
            self.clear()
            self._loading_label.draw()
            self.flip()                     # put what was drawn on screen
        except Exception:
            self._loading_label = None

    def _check_position(self, dt):
        """Make sure the window really ended up at its saved position, and
        move it there if the window manager put it somewhere else.

        Runs a short time after the window appears, and again after each
        correction. At most three checks are made:
          1st check: if the window is not where we want it, move it now that
                     it is on screen.
          2nd check: if it is still a little off (typically by the height of
                     the title bar), move it by the difference.
          3rd check: give up (and say so) rather than fight the window manager."""
        if self._wanted_pos is None:
            return
        x, y = self._wanted_pos
        try:
            cx, cy = self.get_location()
        except Exception:
            self._wanted_pos = None
            return
        dx, dy = x - cx, y - cy
        if abs(dx) <= 2 and abs(dy) <= 2:       # already there: nothing to do
            self._wanted_pos = None
            return
        self._pos_attempts += 1
        if self._pos_attempts == 1:
            self.set_location(x, y)
        elif self._pos_attempts == 2 and abs(dx) <= 100 and abs(dy) <= 100:
            # A small, steady error is a frame/title-bar offset: compensate.
            # (A big error means the window did not move at all, and moving
            # it further would only make things worse.)
            self.set_location(x + dx, y + dy)
        else:
            say(f"note: the window manager did not place the window at its "
                f"saved position ({x}, {y}); it is at ({cx}, {cy}).")
            self._wanted_pos = None
            return
        # Window moves are carried out asynchronously: look again shortly.
        pyglet.clock.schedule_once(self._check_position, 0.2)

    def on_move(self, x, y):
        """pyglet calls this when the window is moved. The latest position is
        remembered so that it can still be saved if the window cannot be asked
        for its position at the moment it is closed."""
        self._last_pos = (x, y)

    @staticmethod
    def _position_ok(x, y):
        """True if a window whose top-left corner is at (x, y) would have its
        title bar reachable on some monitor. This guards against restoring a
        position from a monitor that is no longer connected (or the strange
        coordinates Windows reports for a minimised window)."""
        for s in _screens():
            if (s.x <= x <= s.x + s.width - 100
                    and s.y <= y <= s.y + s.height - 100):
                return True
        return False

    # -- layout ------------------------------------------------------------
    def _compute_layout(self):
        """Work out card size and pile positions from the window size. All
        positions elsewhere are derived from the numbers computed here."""
        w, h = self.width, self.height
        # Card width is limited either by the window width (7 columns must
        # fit) or by its height (room for the top row plus a fanned column).
        cw = min(w / WIDTH_FIT, (h - BAR) / HEIGHT_FIT * ASPECT)
        # Whole pixels (crisper images), never below 40. The height follows
        # from the width so cards keep the proportions of the pictures.
        self.cw = max(40, int(cw))
        self.ch = int(round(self.cw / ASPECT))
        # Space between columns, capped so very wide windows do not spread
        # the piles too far apart; the whole block is then centred.
        self.gap = min((w - 7 * self.cw) / 8, 0.7 * self.cw)
        self.left = (w - 7 * self.cw - 6 * self.gap) / 2
        # y of the top row (stock, waste, foundations) and of the first card
        # in each tableau column (remember: y grows upward).
        self.top_y = round(h - BAR - 0.10 * self.ch - self.ch)
        self.tab_y = round(self.top_y - 0.16 * self.ch - self.ch)
        # Vertical spacing inside a tableau column, and the sideways spacing
        # of the fanned waste cards.
        self.down_off = 0.134 * self.ch     # between face-down cards
        self.up_off = 0.28 * self.ch        # between face-up cards
        self.fan_off = 0.20 * self.ch

    def col_x(self, i):
        """x position of column i (0..6) of the 7-column grid."""
        return round(self.left + i * (self.cw + self.gap))

    def slot_pos(self, kind, i):
        """Bottom-left corner of a pile's slot.
        Top row: stock, waste, (gap column), then four foundations."""
        if kind == "stock":
            return self.col_x(0), self.top_y
        if kind == "waste":
            return self.col_x(1), self.top_y
        if kind == "found":
            return self.col_x(3 + i), self.top_y
        return self.col_x(i), self.tab_y                 # "tab"

    def _build_ui(self):
        """Create the non-card visuals once. Their sizes and positions are
        set by apply_layout(), which also runs after every resize."""
        w, h = self.width, self.height
        self.bg = shapes.Rectangle(0, 0, w, h, color=(12, 102, 58))
        # Optional table picture: if background.png was found, it replaces
        # the plain green rectangle (which stays as the fall-back).
        self.bg_sprite = None
        if self._bg_path:
            tex = load_background(self._bg_path)
            if tex is not None:
                self.bg_sprite = pysprite.Sprite(tex)
        self.top_bar = shapes.Rectangle(0, h - BAR, w, BAR, color=(8, 70, 40))

        # One marker for every place a card pile can be.
        self.slots = [Slot("stock", 0, self.assets),
                      Slot("waste", 0, self.assets)]
        self.slots += [Slot("found", i, self.assets, "A") for i in range(4)]
        self.slots += [Slot("tab", i, self.assets, "K") for i in range(7)]

        # The ring shown on the stock slot once the stock is empty (click it
        # to recycle the waste). Two circles: a big light one with a smaller
        # one in the slot colour on top makes a ring.
        if self.assets.empty:
            outer, inner = (232, 218, 208), self.assets.empty_color
        else:
            outer, inner = SLOT_EDGE, SLOT_FILL
        # (Their real position and radius are set in apply_layout.)
        self.ring = [shapes.Circle(0, 0, 10, color=outer),
                     shapes.Circle(0, 0, 8, color=inner)]

        # Top-bar buttons, in two rows. `by1` / `by2` are the y positions of
        # the two rows (see ROW1_DROP / ROW2_DROP). Each button gets a
        # callback, the function to run when it is clicked.
        by1 = h - ROW1_DROP
        by2 = h - ROW2_DROP
        self.btns = []
        x = 20                              # where the next row-1 button starts

        def add_button(text, width, callback):
            """Create a row-1 button at the next free spot, 10 px after the
            previous one, and remember it in self.btns."""
            nonlocal x
            b = Button(text, x, by1, width, 32, callback, drop=ROW1_DROP)
            self.btns.append(b)
            x += width + 10
            return b

        # Row 1, left to right. The lambda is a tiny anonymous function that
        # toggles the draw count between 1 and 3.
        add_button("New Game", 100, self.new_game)
        add_button("Undo", 70, self.undo)
        add_button("Auto", 70, self.start_auto)
        add_button("Check Moves", 115, self.check_moves)
        self.btn_draw = add_button(
            f"Draw: {self.draw_count}", 85,
            lambda: self.set_draw(1 if self.draw_count == 3 else 3))
        # Only offer "Card Faces" if there is more than one set of faces.
        if len(self.assets.names) > 1:
            add_button("Card Faces", 105, self.cycle_faces)
        # Only offer "Card Back" if some set has more than one back.
        if self.assets.max_backs > 1:
            add_button("Card Back", 95, self.cycle_back)
        # Only offer the sound button if sound files were found.
        self.btn_sound = None
        if self.sounds.available:
            self.btn_sound = add_button("Sound: On", 90, self.toggle_sound)
        # Row 2: the Reset Stats button stays 20 px from the right edge (its x
        # is set in apply_layout, which knows the window width).
        self.btn_reset = Button("Reset Stats", 0, by2, 130, 26, self.reset_stats,
                                drop=ROW2_DROP, right=20)
        self.btns.append(self.btn_reset)

        # Row 2 text: moves/time on the left, wins/losses next to the Reset
        # button on the right. (Positions are set in apply_layout.)
        self.info = make_label("", font_size=13, x=20, y=by2 + 13,
                               anchor_x="left", anchor_y="center",
                               color=(235, 245, 235, 255))
        self.stats_lbl = make_label("", font_size=13, x=w - 164, y=by2 + 13,
                                    anchor_x="right", anchor_y="center",
                                    color=(235, 245, 235, 255))
        # The "You won!" message (drawn twice, black offset by 2px, to make a
        # drop shadow).
        msg = "You won!  Press N for a new game"
        self.win_lbl = make_label(msg, weight="bold", font_size=30, x=w / 2,
                                  y=h / 2 - 40, anchor_x="center",
                                  anchor_y="center", color=(255, 235, 120, 255))
        self.win_shadow = make_label(msg, weight="bold", font_size=30, x=w / 2 + 2,
                                     y=h / 2 - 42, anchor_x="center",
                                     anchor_y="center", color=(0, 0, 0, 255))
        # Banner shown when Check Moves finds no useful moves (with a shadow).
        smsg = "No more moves!   Press U to undo or N for a new game"
        self.stuck_lbl = make_label(smsg, weight="bold", font_size=22, x=w / 2,
                                    y=h / 2 - 40, anchor_x="center",
                                    anchor_y="center", color=(255, 170, 150, 255))
        self.stuck_shadow = make_label(smsg, weight="bold", font_size=22,
                                       x=w / 2 + 2, y=h / 2 - 42,
                                       anchor_x="center", anchor_y="center",
                                       color=(0, 0, 0, 255))
        # A short-lived notice (e.g. "Moves are still available"); its text
        # is filled in by show_notice().
        self.notice_lbl = make_label("", weight="bold", font_size=22, x=w / 2,
                                     y=h / 2 - 40, anchor_x="center",
                                     anchor_y="center", color=(190, 255, 190, 255))
        self.notice_shadow = make_label("", weight="bold", font_size=22, x=w / 2 + 2,
                                        y=h / 2 - 42, anchor_x="center",
                                        anchor_y="center", color=(0, 0, 0, 255))

    def apply_layout(self):
        """Reposition / rescale everything for the current window size."""
        self._compute_layout()
        w, h = self.width, self.height
        cw, ch = self.cw, self.ch
        self._laid_out_size = (w, h)        # remember what this layout is for

        # Background, top bar, buttons and text follow the window edges.
        self.bg.width, self.bg.height = w, h
        if self.bg_sprite:
            # "Cover" scaling: enlarge the picture just enough to fill the
            # whole window without distorting it, centred. Whatever sticks
            # out past the window edges is simply not shown.
            sprite = self.bg_sprite
            tw, th = sprite.image.width, sprite.image.height
            scale = max(w / tw, h / th)
            sprite.scale = scale
            sprite.x = (w - tw * scale) / 2
            sprite.y = (h - th * scale) / 2
        self.top_bar.y, self.top_bar.width = h - BAR, w
        for b in self.btns:
            b.set_y(h - b.drop)             # each button keeps its distance from the top
            if b.right is not None:         # right-aligned buttons follow the right edge
                b.set_x(w - b.right - b.w)
        # Row 2 text sits vertically in the middle of the 26 px row.
        row2_mid = h - ROW2_DROP + 13
        self.info.x, self.info.y = 20, row2_mid
        # Wins/losses end 14 px to the left of the Reset Stats button.
        self.stats_lbl.x, self.stats_lbl.y = self.btn_reset.x - 14, row2_mid
        # The three centred banners (won / no more moves / notice).
        for lbl, dx, dy in ((self.win_lbl, 0, 0), (self.win_shadow, 2, -2),
                            (self.stuck_lbl, 0, 0), (self.stuck_shadow, 2, -2),
                            (self.notice_lbl, 0, 0), (self.notice_shadow, 2, -2)):
            lbl.x, lbl.y = w / 2 + dx, h / 2 - 40 + dy

        # Empty-pile markers and the stock ring.
        for s in self.slots:
            x, y = self.slot_pos(s.kind, s.idx)     # where this pile lives
            s.layout(x, y, cw, ch)
        sx, sy = self.slot_pos("stock", 0)
        # zip() pairs each circle with its radius: outer 21% of the card
        # height, inner 16.5%, which leaves a ring between them.
        for c, r in zip(self.ring, (0.21 * ch, 0.165 * ch)):
            c.x, c.y, c.radius = sx + cw / 2, sy + ch / 2, r

        # Every card is rescaled to the new card size.
        for c in self.cards:
            c.resize(cw, ch)

        # Abort any drag.
        if self.drag:
            for c in self.drag["cards"]:
                c.dragging = False
            self.drag = None
        # Running animations store pixel coordinates from the OLD layout, so
        # they cannot simply carry on.
        if self.dealing:
            # The size changed in the middle of the deal. This also happens
            # right after the window first appears (many systems send a
            # resize then), so just snapping everything into place would
            # cut the opening deal short. Start the deal again at the new
            # size instead, so it is always seen.
            self._animate_deal()
            return
        # Otherwise jump every card straight to its new place.
        # targets() returns {card: (x, y)}; .items() loops over its pairs, and
        # `(tx, ty)` in the loop header unpacks each position tuple.
        for c, (tx, ty) in self.targets().items():
            if c.launched:                  # win-celebration cards keep flying
                continue
            c.snap(tx, ty)
            if c.pending_flip:              # dealt card that was still to flip
                c.pending_flip = False
                c.face_up = True
                c.flip_t = None

    def on_resize(self, width, height):
        """pyglet calls this whenever the window size changes."""
        super().on_resize(width, height)    # let pyglet fix the viewport
        # getattr(obj, name, default) reads an attribute that might not exist
        # yet: pyglet calls on_resize while the window is still being built,
        # before __init__ has reached `self._ready = True`.
        # A resize event that does not change the size (some systems send one
        # right after the window appears) needs no new layout.
        if getattr(self, "_ready", False) and (width, height) != self._laid_out_size:
            self.apply_layout()

    def targets(self):
        """Where every card should be, given the current logical state.

        Returns a dict {card: (x, y)}. This is the single place that turns
        the piles (logical state) into screen positions (visual state)."""
        T = {}                              # card -> (x, y), filled in below
        # Stock: every card sits exactly on the stock slot.
        sx, sy = self.slot_pos("stock", 0)
        for c in self.stock:
            T[c] = (sx, sy)

        # Waste: the top cards are fanned to the right (draw-3 mode). `fan`
        # is how many cards are fanned; `k` is a card's distance from the top
        # (0 = top card, which sits furthest right).
        wx, wy = self.slot_pos("waste", 0)
        n = len(self.waste)
        fan = min(max(1, self.waste_fan), 3) if self.draw_count == 3 else 1
        for i, c in enumerate(self.waste):
            k = n - 1 - i                               # 0 = top card
            off = (fan - 1 - k) * self.fan_off if k < fan else 0
            T[c] = (wx + off, wy)

        # Foundations: cards are stacked exactly on top of each other.
        for i, pile in enumerate(self.found):
            fx, fy = self.slot_pos("found", i)
            for c in pile:
                T[c] = (fx, fy)

        # Tableau: each card sits a bit lower than the one before it, so the
        # cards below are still visible. Face-down cards use a smaller step.
        for i, col in enumerate(self.tab):
            x, y0 = self.slot_pos("tab", i)
            # `d` / `u` are the vertical steps after a face-down / face-up card.
            # Normally they are the standard spacing; a very long column is
            # squeezed so that it still fits above the bottom of the window.
            body = col[:-1]                 # every card that has one below it
            n_up = sum(1 for c in body if c.face_up)
            n_down = len(body) - n_up
            avail = y0 - 0.12 * self.ch     # vertical room above the window bottom
            d, u = self.down_off, self.up_off
            if n_down * d + n_up * u > avail:      # long column: squeeze it
                if n_down:                         # face-down cards first
                    d = min(d, max(0.07 * self.ch, (avail - n_up * u) / n_down))
                if n_up and n_down * d + n_up * u > avail:
                    u = max(0.08 * self.ch, (avail - n_down * d) / n_up)
            y = y0
            for j, c in enumerate(col):
                T[c] = (x, y)
                if j < len(body):
                    y -= u if c.face_up else d      # next card goes lower
        return T

    def relayout(self, delays=None, zs=None, dur=None):
        """Animate every card to where the logical state says it belongs.

        delays  optional {card: seconds} start delays (used to stagger the
                deal and stock draws)
        zs      optional {card: z} drawing order overrides
        dur     optional fixed slide duration in seconds
        Cards that are already in the right place (or already heading there)
        are ignored by Card.move_to, so calling this is always safe."""
        delays = delays or {}               # `None or {}` gives a fresh empty dict
        zs = zs or {}
        T = self.targets()                  # where every card should be
        # Visit the piles in a fixed order; move_to hands out increasing z
        # values in this order, so later cards are drawn over earlier ones.
        order = list(self.stock) + list(self.waste)
        for p in self.found:
            order += p
        for p in self.tab:
            order += p
        for c in order:
            tx, ty = T[c]
            c.move_to(tx, ty, dur, delays.get(c, 0.0), zs.get(c))

    # -- piles helpers -----------------------------------------------------
    # A "pile reference" is a small tuple naming a pile, e.g. ("tab", 3),
    # ("found", 0), ("waste", 0) or ("stock", 0).
    def pile_of(self, ref):
        """Return the actual list for a pile reference."""
        kind, i = ref
        if kind == "stock":
            return self.stock
        if kind == "waste":
            return self.waste
        if kind == "found":
            return self.found[i]
        return self.tab[i]

    def all_piles(self):
        """Yield (kind, index, list) for every pile."""
        yield "stock", 0, self.stock
        yield "waste", 0, self.waste
        for i, p in enumerate(self.found):
            yield "found", i, p
        for i, p in enumerate(self.tab):
            yield "tab", i, p

    def can_drop(self, cards, dst, cheat=False):
        """The Klondike rules: may this run of `cards` be placed on the pile
        `dst`? `cards[0]` is the card that would touch the destination.
        With `cheat` (Shift+Ctrl held while dropping) any card or run is also
        accepted by an EMPTY tableau column, not just a king."""
        kind, i = dst
        lead = cards[0]
        if kind == "found":
            # Foundations take one card at a time: an ace on an empty pile,
            # then the next rank of the same suit.
            if len(cards) != 1:
                return False
            pile = self.found[i]
            if not pile:
                return lead.rank == 1
            top = pile[-1]
            return top.suit == lead.suit and lead.rank == top.rank + 1
        if kind == "tab":
            # Tableau: only a king on an empty column; otherwise one rank
            # lower and the opposite colour of the (face-up) card underneath
            # (for example a red 6 may go on a black 7, never on a red 7).
            pile = self.tab[i]
            if not pile:
                return lead.rank == 13 or cheat
            top = pile[-1]
            return top.face_up and top.rank == lead.rank + 1 and top.red != lead.red
        return False                        # you can never drop on stock/waste

    def find_foundation(self, card):
        """Index of a foundation that accepts `card`, or None."""
        for i in range(4):
            if self.can_drop([card], ("found", i)):
                return i
        return None

    def reachable_waste_tops(self):
        """Every card that can ever become the PLAYABLE (top) card of the
        waste if the player just keeps clicking the stock.

        This depends on the draw mode: with draw-3 only every third card of
        the stock ever ends up on top, so some cards can never be played
        without other cards being moved first. We find out by simulating the
        clicks on COPIES of the piles. Clicking never changes anything else,
        so the sequence of (stock, waste) states repeats after a while; once
        a state comes round again we have seen every card that can appear."""
        stock, waste = list(self.stock), list(self.waste)   # copies: no side effects
        n = self.draw_count
        tops = []
        if waste:
            tops.append(waste[-1])          # playable right now
        # A state is described by the identity of the cards in each pile.
        seen = {(tuple(map(id, stock)), tuple(map(id, waste)))}
        # The limit is only a safety net; the loop normally ends much sooner.
        for _ in range(4 * (len(stock) + len(waste)) + 4):
            if stock:
                # Same as click_stock(): turn over up to n cards.
                for _ in range(min(n, len(stock))):
                    waste.append(stock.pop())
            elif waste:
                # Stock empty: recycle the waste (this reverses its order).
                while waste:
                    stock.append(waste.pop())
            else:
                break                       # nothing to click at all
            state = (tuple(map(id, stock)), tuple(map(id, waste)))
            if state in seen:               # back where we started: done
                break
            seen.add(state)
            if waste:
                tops.append(waste[-1])      # the newly exposed playable card
        return tops

    def has_useful_move(self):
        """False when the game is stuck: no move remains that could make
        progress. Used by the Check Moves button.

        A move counts as progress when it is one of these:
          1. a card goes up to a foundation,
          2. a card that can reach the top of the waste goes onto a column,
          3. a tableau run moves and turns over a face-down card, or a king
             moves onto an empty column (from the middle of a column).
        Other moves (e.g. shuffling a run back and forth between two columns)
        do not count, otherwise the game could never be "stuck".

        This is a practical check, not a full solver: a position that could
        only be rescued by a long chain of "pointless" shuffles would be
        reported as stuck."""
        tops = self.reachable_waste_tops()              # playable via the stock
        bottoms = [col[-1] for col in self.tab if col]  # playable tableau cards
        # 1. Anything that can go up to a foundation?
        for c in tops + bottoms:
            if self.find_foundation(c) is not None:
                return True
        # 2. Any waste card (that can ever be on top) that fits on a column?
        for c in tops:
            for i in range(7):
                if self.can_drop([c], ("tab", i)):
                    return True
        # 3. Any tableau run that can move somewhere useful?
        for i, col in enumerate(self.tab):
            for j, lead in enumerate(col):
                if not lead.face_up:
                    continue
                # Moving col[j:] away would expose col[j-1]; useful if that
                # card is face down (it then gets turned over).
                uncovers = j > 0 and not col[j - 1].face_up
                for k in range(7):
                    if k == i or not self.can_drop(col[j:], ("tab", k)):
                        continue
                    king_to_empty = lead.rank == 13 and j > 0 and not self.tab[k]
                    if uncovers or king_to_empty:
                        return True
        return False

    @property
    def locked(self):
        """True while the board should ignore the player's input."""
        return self.dealing or self.auto or self.win_pending or self.won

    # -- new game / deal ---------------------------------------------------
    def new_game(self):
        """Shuffle and deal a fresh game (New Game button / N key)."""
        # Leaving a game that was played but not won counts as a loss. (A game
        # that has had no moves yet, or was already won, does not.)
        if self.game_active and self.moves > 0:
            self.losses += 1
            self.save_settings()
        self.game_active = True             # the game we are about to deal
        # Cancel anything left over from the previous game.
        pyglet.clock.unschedule(self._auto_step)
        self.sounds.stop_long()             # silence any applause / game-over clip
        self.auto = False
        self.won = self.win_pending = False
        self.win_queue, self.win_idx, self.win_time = [], 0, 0.0
        self.drag = None
        self.last_click = None

        # Shuffle, then put every card face down on the stock slot.
        # `self.cards[:]` is a COPY of the list, so shuffling it leaves
        # self.cards (the fixed list of all 52 cards) in its original order.
        deck = self.cards[:]
        random.shuffle(deck)
        sx, sy = self.slot_pos("stock", 0)
        for c in deck:
            c.face_up = False
            c.flip_t = None
            c.pending_flip = False
            c.dragging = c.launched = False
            c._kf = c._kb = None
            c.snap(sx, sy)

        # Fresh piles: the whole shuffled deck starts in the stock.
        # (`[[] for _ in range(4)]` builds four SEPARATE empty lists.)
        self.stock = deck
        self.waste = []
        self.found = [[] for _ in range(4)]
        self.tab = [[] for _ in range(7)]
        self.waste_fan = 0
        self.undo_stack = []
        self.moves = 0
        self.elapsed = 0.0
        self.timer_on = False
        self.stuck = False                  # hide the "no more moves" banner
        self.notice_time = 0.0

        # Deal like a real game: row by row, one card to each column that
        # still needs one (column c gets c+1 cards; its last card faces up).
        # The piles are filled instantly; the animation catches up in
        # _animate_deal. Row 0 gives a card to columns 0-6, row 1 to columns
        # 1-6, and so on, so column c ends up with c + 1 cards.
        for row in range(7):
            for col in range(row, 7):
                self.tab[col].append(self.stock.pop())
        self._animate_deal()

    def _animate_deal(self):
        """Show the cards being dealt from the stock into the tableau.

        The piles must already be dealt (see new_game). Every card is put
        back face down on the stock slot, and then each one is given a start
        delay so that they leave the stock one after another. It may be
        called again if the window changes size during the deal (see
        apply_layout), which simply starts the animation over."""
        sx, sy = self.slot_pos("stock", 0)
        # `deal` lists the dealt cards in dealing order, with True for the
        # card that will be turned face up (the last one in its column).
        deal = []
        for row in range(7):
            for col in range(row, 7):
                deal.append((self.tab[col][row], col == row))
        # Everything starts face down on the stock.
        for c in self.cards:
            c.face_up = False
            c.flip_t = None
            c.pending_flip = False
            c.dragging = c.launched = False
            c._kf = c._kb = None
            c.snap(sx, sy)
        # Give each dealt card a start delay so they leave the stock one
        # after another. Earlier cards get a slightly higher z so that they
        # sit on top of the ones still waiting on the stock.
        base = next_z()
        delays, zs = {}, {}
        for k, (c, up) in enumerate(deal):
            delays[c] = k * 0.06
            zs[c] = base + (len(deal) - k) * 0.001    # earlier cards on top
            c.pending_flip = up                        # flip on arrival
            c.land_sound = "card_placement"            # thump as each card lands
        self.dealing = True
        self.relayout(delays=delays, zs=zs, dur=0.32)

    def set_draw(self, n):
        """Switch between draw-1 and draw-3 (starts a new game)."""
        if n == self.draw_count:
            return
        self.draw_count = n
        self.btn_draw.set_text(f"Draw: {n}")
        self.new_game()                     # (counts the unfinished game as a loss)
        self.save_settings()                # remember the new draw mode

    def cycle_back(self):
        """Switch to the next card back image."""
        if self.assets.cycle_back():
            tex = self.assets.current_back()
            for c in self.cards:
                c.set_back_texture(tex)
            self.save_settings()            # remember the chosen card back

    def cycle_faces(self):
        """Switch to the next set of card faces (Card Faces button / F key).

        A set that has been used before switches at once. A set that has not
        been read yet takes a moment (longer the very first time, before its
        cache file exists), and the window cannot be redrawn while it loads.
        So the "Loading card faces..." message is shown first and the real
        work is done a few frames later, after the message has been drawn."""
        nxt = self.assets.next_name()
        if nxt is None or self._faces_switch_pending:
            return                          # only one set, or already switching
        if self.assets.is_loaded(nxt):
            self._switch_faces()
            return
        self._faces_switch_pending = True
        self.show_notice("Loading card faces...", 60.0)
        pyglet.clock.schedule_once(self._switch_faces, 0.05)

    def _switch_faces(self, dt=0):
        """Do the switch to the next card set (loading it first if needed)."""
        self._faces_switch_pending = False
        self.notice_time = 0.0              # remove the "Loading..." message
        if self.assets.cycle_faces():
            self._refresh_visuals()
            self.save_settings()            # remember the chosen card faces

    def _refresh_visuals(self):
        """Give every card, every empty-pile marker and the stock ring the
        pictures of the selected card set. Positions and animations are left
        alone, so this can be done in the middle of a game."""
        a = self.assets
        back, empty = a.current_back(), a.empty     # (these may load a set)
        for c in self.cards:
            # None means "this set has no picture for the card": it is then
            # drawn with shapes until a set that has one is selected.
            c.set_face_texture(a.faces.get((c.rank, c.suit)))
            c.set_back_texture(back)
        for s in self.slots:
            s.set_texture(empty)
            x, y = self.slot_pos(s.kind, s.idx)
            s.layout(x, y, self.cw, self.ch)
        # The ring that marks an empty stock matches the marker's colour.
        if empty:
            self.ring[0].color, self.ring[1].color = (232, 218, 208), a.empty_color
        else:
            self.ring[0].color, self.ring[1].color = SLOT_EDGE, SLOT_FILL

    # -- statistics, notices and saved settings ----------------------------
    def check_moves(self):
        """The Check Moves button (or C key): tell the player whether any
        useful move is left. Nothing is checked automatically; the player
        decides when to ask."""
        if self.locked:                     # dealing, auto-playing, or game won
            return
        if self.has_useful_move():
            self.stuck = False
            self.show_notice("Moves are still available")
        else:
            if not self.stuck:              # announce once, not on every press
                self.play("lose_game", long=True)
            self.stuck = True
            self.notice_time = 0.0

    def show_notice(self, text, seconds=2.5):
        """Show a short message in the middle of the window for a moment."""
        self.notice_lbl.text = text
        self.notice_shadow.text = text
        self.notice_time = seconds

    def _record_win(self):
        """Count a win (called once, when the last card reaches a foundation).
        The clock stops at this moment, so self.elapsed is the winning time."""
        self.wins += 1
        # Keep the shortest time seen so far.
        if self.best_time is None or self.elapsed < self.best_time:
            self.best_time = self.elapsed
        self.game_active = False            # this game is over: no loss later
        self.save_settings()

    def reset_stats(self):
        """The Reset Stats button. To prevent accidents it must be clicked
        twice within a few seconds; the first click only arms it."""
        if self.reset_armed <= 0:
            self.reset_armed = 3.0
            self.btn_reset.set_text("Click to confirm")
        else:
            self.wins = self.losses = 0
            self.best_time = None           # the fastest win is a statistic too
            self.reset_armed = 0.0
            self.btn_reset.set_text("Reset Stats")
            self.save_settings()

    def save_settings(self):
        """Write everything worth remembering to settings.json: window size
        and position, card faces, card back, draw mode and the statistics. This never
        raises; a failure only prints a warning (once)."""
        data = dict(self.settings)          # start from what we loaded
        data["version"] = 1
        data["draw_count"] = self.draw_count
        data["wins"] = self.wins
        data["losses"] = self.losses
        if self.best_time is None:
            data.pop("best_time", None)     # nothing to remember (or just reset)
        else:
            data["best_time"] = round(self.best_time, 2)
        faces = self.assets.current_name()
        if faces:
            data["card_faces"] = faces
        back = self.assets.current_back_name()
        if back:
            data["card_back"] = back
        win = data.get("window")
        win = dict(win) if isinstance(win, dict) else {}
        win["width"], win["height"] = self.width, self.height
        # Ask the window where it is; if that fails (or gives nonsense, such as
        # the coordinates of a minimised window), use the last position that
        # on_move reported. If neither is usable the old saved position stays.
        pos = None
        try:
            pos = self.get_location()
        except Exception:
            pass
        if pos is None or not self._position_ok(*pos):
            pos = self._last_pos
        if pos is not None and self._position_ok(*pos):
            win["x"], win["y"] = pos
        data["window"] = win
        self.settings = data
        try:
            write_settings(data)
        except Exception as e:
            if not self._warned_settings:
                self._warned_settings = True
                say(f"warning: could not save settings: {e}")

    def on_close(self):
        """pyglet calls this when the window is closed (the X button, or Esc).

        A game that is still being played counts as a loss if no useful move
        is left, even if the player never pressed Check Moves. (A game that
        still has moves is simply left unfinished: not counted.) The check is
        skipped during the deal, when the cards are still being turned over
        and the position is not final. Afterwards the settings are saved,
        including the final window size and position."""
        if (self.game_active and not self.dealing
                and (self.stuck or not self.has_useful_move())):
            self.losses += 1
            self.game_active = False        # never count the same game twice
        self.save_settings()
        super().on_close()

    # -- sound -------------------------------------------------------------
    def play(self, name, volume=1.0, long=False):
        self.sounds.play(name, volume, long)

    def _card_sound(self, name):
        """Called by a Card when it wants to make a sound (a flip, or landing
        after a slide). Sounds are quieter during the deal so the 28 quick
        thumps do not drown everything out."""
        if name == "flip" and self.silent_flips:
            return                          # a bulk flip; the caller plays one sound
        self.play(name, 0.6 if self.dealing else 1.0)

    def toggle_sound(self):
        """Mute / unmute (M key or the Sound button)."""
        self.sounds.enabled = not self.sounds.enabled
        if not self.sounds.enabled:
            self.sounds.stop_all()
        if self.btn_sound:
            self.btn_sound.set_text("Sound: On" if self.sounds.enabled else "Sound: Off")

    def _play_landing(self, card):
        """Play the card-placement sound when `card` finishes moving (or at
        once if it is not moving because it is already in place)."""
        if card.animating:
            card.land_sound = "card_placement"
        else:
            self.play("card_placement")

    # -- undo --------------------------------------------------------------
    # Undo works by saving a snapshot of the piles BEFORE each move. Because
    # the piles are just lists of the same Card objects, restoring one means
    # putting the lists back and letting relayout() animate cards home.
    def push_undo(self):
        """Save a snapshot of the game. `list(p)` copies a pile so that later
        changes to the real pile do not alter the snapshot; the Card objects
        themselves are shared, only the lists are copied."""
        self.undo_stack.append(dict(
            stock=list(self.stock), waste=list(self.waste),
            found=[list(p) for p in self.found],
            tab=[list(p) for p in self.tab],
            faces={c: c.face_up for c in self.cards},
            fan=self.waste_fan, moves=self.moves))

    def undo(self):
        """Take back the last move (button, U key or Ctrl+Z)."""
        # Ignore the request while the board is busy or nothing was saved.
        if self.locked or self.drag or not self.undo_stack:
            return
        s = self.undo_stack.pop()
        self.stock, self.waste = s["stock"], s["waste"]
        self.found, self.tab = s["found"], s["tab"]
        self.silent_flips = True            # one sound for the whole undo
        for c, up in s["faces"].items():
            c.set_face(up)                  # flips back cards turned over since
        self.silent_flips = False
        self.waste_fan = s["fan"]
        self.moves = s["moves"]
        self.stuck = False                  # the position changed: hide the banner
        self.play("card_placement")
        self.relayout()

    # -- moves -------------------------------------------------------------
    def click_stock(self):
        """Clicking the stock draws cards; clicking it when it is empty
        turns the waste back over to make a new stock."""
        if self.stock:
            self.push_undo()
            drawn = []
            # Move 1 or 3 cards (fewer if the stock is running out) from the
            # top of the stock to the waste, turning them face up.
            self.silent_flips = True        # play a single flip sound below
            for _ in range(min(self.draw_count, len(self.stock))):
                c = self.stock.pop()
                c.set_face(True)
                self.waste.append(c)
                drawn.append(c)
            self.silent_flips = False
            self.play("flip")
            # Fan out as many cards as were just drawn (draw-3 only). Each drawn
            # card starts 0.08 s after the previous one, so they peel off the
            # stock one by one. (`{...for...}` is a dict comprehension: it
            # builds {card: delay} in a single line.)
            self.waste_fan = len(drawn) if self.draw_count == 3 else 1
            delays = {c: k * 0.08 for k, c in enumerate(drawn)}
            self.moves += 1
            self.timer_on = True            # the first draw also starts the clock
            self.relayout(delays=delays)
        elif self.waste:                                  # recycle the waste
            self.push_undo()
            delays = {}
            k = 0
            # Popping from the waste and pushing onto the stock reverses the
            # order, so the first card originally drawn is on top again.
            self.silent_flips = True        # one "refill" sound instead
            while self.waste:
                c = self.waste.pop()
                c.set_face(False)
                self.stock.append(c)
                delays[c] = k * 0.012
                k += 1
            self.silent_flips = False
            self.play("refill_stock")
            self.waste_fan = 0
            # Turning the waste back over is deliberately NOT counted as a
            # move (it can be undone, but the move counter does not change).
            self.relayout(delays=delays)

    def do_move(self, cards, src, dst):
        """Carry out a move that has already been checked with can_drop().
        `cards` are the last len(cards) cards of pile `src`."""
        self.push_undo()                    # remember the position first
        spile = self.pile_of(src)           # the real list of the source pile
        # `spile[n:]` is the tail of a list from index n. The moved cards are
        # always the last len(cards) items, so delete exactly that tail.
        del spile[len(spile) - len(cards):]          # take them off the source
        self.pile_of(dst).extend(cards)              # ...and add to the target
        if src[0] == "waste":
            # One fewer card in the waste fan.
            self.waste_fan = max(0, self.waste_fan - 1)
        if src[0] == "tab" and spile and not spile[-1].face_up:
            spile[-1].set_face(True)        # uncovered card turns face up
        self.moves += 1
        self.timer_on = True                # the first move starts the clock
        self.stuck = False                  # the position changed: hide the banner
        self.relayout()                     # animate everything to its new place
        self._play_landing(cards[0])        # "thump" when the lead card lands
        if sum(len(p) for p in self.found) == 52 and not self.win_pending:
            self.win_pending = True         # celebration starts once cards land
            self._record_win()              # the game is won: count it now

    def try_auto_foundation(self, card):
        """Send `card` to a foundation if it is the playable card of its pile
        and the rules allow it. Returns True if a move was made."""
        # Only the waste's top card and the bottom card of a column can go up.
        # `pile[-1] is card` checks it is the very same object, not merely an
        # equal-looking card.
        for kind, i, pile in self.all_piles():
            if kind in ("waste", "tab") and pile and pile[-1] is card and card.face_up:
                dst = self.find_foundation(card)
                if dst is not None:
                    self.do_move([card], (kind, i), ("found", dst))
                    return True
        return False

    # -- auto play ---------------------------------------------------------
    def start_auto(self):
        """Repeatedly move any playable card to a foundation (Auto button)."""
        if self.locked:
            return
        self.auto = True
        pyglet.clock.schedule_once(self._auto_step, 0.05)

    def _auto_step(self, dt):
        """Make one automatic move, then schedule the next one shortly after
        so each card is seen moving. Stops when nothing can move."""
        # Candidate piles to take a card from: the waste and every column.
        refs = []
        if self.waste:
            refs.append(("waste", 0))
        refs += [("tab", i) for i, col in enumerate(self.tab) if col]
        for ref in refs:
            card = self.pile_of(ref)[-1]
            if not card.face_up:
                continue
            dst = self.find_foundation(card)
            if dst is not None:
                self.do_move([card], ref, ("found", dst))
                pyglet.clock.schedule_once(self._auto_step, 0.16)
                return
        self.auto = False                   # no more moves: unlock the board

    # -- hit testing / mouse -----------------------------------------------
    # Mouse input is a three-step conversation with pyglet:
    #   press   -> pick up a card (or click a button / the stock)
    #   drag    -> move the picked-up cards along with the pointer
    #   release -> decide what the drop means: a move, a snap back, or a click
    def _inside(self, c, x, y):
        """True if the point (x, y) is inside card c's current rectangle."""
        return c.x <= x <= c.x + self.cw and c.y <= y <= c.y + self.ch

    def hit_test(self, x, y):
        """Return (source_ref, run_of_cards) for the grabbable card at x, y.

        Dragging a tableau card takes it and every card below it (a "run").
        Returns None if there is nothing grabbable at that point."""
        for i, col in enumerate(self.tab):
            # Search from the bottom-most (front) card up, because cards
            # overlap and the front card is the one the player sees.
            for j in range(len(col) - 1, -1, -1):
                c = col[j]
                if self._inside(c, x, y):
                    # `col[j:]` = this card and every card after it (the run).
                    # A face-down card cannot be picked up: return None.
                    return (("tab", i), col[j:]) if c.face_up else None
        if self.waste and self._inside(self.waste[-1], x, y):
            return ("waste", 0), [self.waste[-1]]
        for i, p in enumerate(self.found):
            if p and self._inside(p[-1], x, y):
                return ("found", i), [p[-1]]
        return None

    def on_mouse_press(self, x, y, button, modifiers):
        """pyglet calls this when a mouse button goes down at (x, y)."""
        # Buttons work at any time (even while the board is locked).
        for b in self.btns:
            if button == mouse.LEFT and b.contains(x, y):
                b.callback()
                return
        if self.locked:
            return

        # Right-click: send the card straight to a foundation.
        if button == mouse.RIGHT:
            hit = self.hit_test(x, y)
            if hit and not self.try_auto_foundation(hit[1][0]):
                self.play("illegal")        # that card cannot go up
            return
        if button != mouse.LEFT:
            return

        # Click on the stock slot: draw cards / recycle.
        sx, sy = self.slot_pos("stock", 0)
        if sx <= x <= sx + self.cw and sy <= y <= sy + self.ch:
            self.click_stock()
            return

        # Otherwise start dragging the card (or run) under the mouse.
        hit = self.hit_test(x, y)
        if not hit:
            return
        src, run = hit
        lead = run[0]                       # the card actually grabbed
        base_z = next_z()                   # dragged cards draw above the rest
        for k, c in enumerate(run):
            c.animating = False             # stop any slide in progress
            c.land_sound = None
            c.dragging = True               # the mouse now controls it
            c.tx, c.ty = c.x, c.y
            c.z = base_z + k * 0.001        # keep the run in order
        # Remember where inside the card we grabbed it (gx, gy) and the
        # offset of each other card in the run relative to the lead card.
        # self.drag holds: cards = the run being dragged, src = the pile it
        # came from, gx/gy = grab point inside the lead card, px/py = where
        # the mouse went down (to tell a click from a drag), and rel = each
        # card's offset from the lead card.
        self.drag = dict(cards=run, src=src, gx=x - lead.x, gy=y - lead.y,
                         px=x, py=y,
                         rel=[(c.x - lead.x, c.y - lead.y) for c in run])

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        """Called repeatedly while the mouse moves with a button held."""
        d = self.drag
        if not d:
            return
        # Move each dragged card so it keeps the same position relative to
        # the mouse pointer as when it was picked up.
        for c, (rx, ry) in zip(d["cards"], d["rel"]):
            c.x = x - d["gx"] + rx
            c.y = y - d["gy"] + ry
            c.tx, c.ty = c.x, c.y

    def on_mouse_release(self, x, y, button, modifiers):
        """Called when the button goes up: this is where a drag is decided."""
        d = self.drag
        if not d or button != mouse.LEFT:
            return
        # 1. The drag is over: forget it and give the cards back to
        #    relayout() (they still sit wherever the mouse dropped them).
        self.drag = None
        cards, src = d["cards"], d["src"]
        for c in cards:
            c.dragging = False              # hand the cards back to relayout()
        lead = cards[0]

        # 2. A click without movement (under 5 pixels): maybe a double-click
        #    -> foundation. `math.hypot(a, b)` is the straight-line distance
        #    sqrt(a*a + b*b).
        if math.hypot(x - d["px"], y - d["py"]) < 5:
            now = time.time()
            if self.last_click and self.last_click[0] is lead and now - self.last_click[1] < 0.4:
                self.last_click = None
                if self.try_auto_foundation(lead):
                    return
                self.play("illegal")        # double-clicked a card that cannot go up
            else:
                self.last_click = (lead, now)
            self.relayout()
            return

        # 3. A real drag: find the valid destination pile with the most overlap.
        # Every candidate pile is turned into a rectangle; the pile whose
        # rectangle overlaps the dragged card most (and accepts it under the
        # rules) wins. For a tableau column the rectangle covers the whole
        # column, so you can drop anywhere along it.
        # The cheat: with both Shift and Ctrl held, can_drop() also lets any
        # card or run go onto an empty tableau column.
        cheat = bool(modifiers & key.MOD_SHIFT and modifiers & key.MOD_CTRL)
        T = self.targets()
        best, best_ov = None, 0
        blocked = False                     # dropped on a pile that refuses it?
        thr = 0.06 * self.cw * self.ch      # minimum overlap that counts
        for kind, n in [("found", i) for i in range(4)] + [("tab", i) for i in range(7)]:
            ref = (kind, n)
            if ref == src:
                continue
            valid = self.can_drop(cards, ref, cheat)
            pile = self.pile_of(ref)
            if pile:
                ys = [T[c][1] for c in pile]
                rx, ry = T[pile[0]][0], min(ys)
                rh = max(ys) + self.ch - ry
            else:
                rx, ry = self.slot_pos(kind, n)
                rh = self.ch
            ov = overlap(lead.x, lead.y, self.cw, self.ch, rx, ry, self.cw, rh)
            if not valid:
                if ov > thr:
                    blocked = True          # it was dropped on a pile that says no
                continue
            if ov > best_ov:
                best, best_ov = ref, ov
        # Require a small minimum overlap so stray drops do not count.
        if best and best_ov > thr:
            self.do_move(cards, src, best)
        else:
            # Invalid drop: the piles are unchanged, so relayout() simply
            # slides the cards back to where they came from. Buzz if the
            # player tried to put them on a pile that does not accept them
            # (a drop on empty table is just a cancelled drag: silent).
            if blocked:
                self.play("illegal")
            self.relayout()

    def on_key_press(self, symbol, modifiers):
        """pyglet calls this for every key press. `symbol` says which key;
        `modifiers` is a bit mask of Ctrl/Shift/... held at the same time."""
        if symbol == key.N:
            self.new_game()
        elif symbol == key.U or (symbol == key.Z and
                                 modifiers & (key.MOD_CTRL | key.MOD_COMMAND)):
            self.undo()
        elif symbol == key.A:
            self.start_auto()
        elif symbol == key.C:
            self.check_moves()
        elif symbol == key.F:
            self.cycle_faces()
        elif symbol == key.B:
            self.cycle_back()
        elif symbol == key.M:
            self.toggle_sound()
        elif symbol == key._1:
            self.set_draw(1)
        elif symbol == key._3:
            self.set_draw(3)
        else:
            super().on_key_press(symbol, modifiers)   # Esc closes the window

    # -- per-frame update ----------------------------------------------------
    def update(self, dt):
        """Runs 60 times a second: advances animations, the clock, and
        the win celebration."""
        # `dt` is the time since the last call. Capping it stops animations
        # jumping ahead if the program stalled (e.g. while the window is dragged).
        dt = min(dt, 0.05)
        for c in self.cards:
            c.update(dt)                    # advance every card's animation

        self.sounds.update()                # free players that have finished
        # `busy` is True while any card is still sliding.
        busy = any(c.animating for c in self.cards)
        if self.dealing and not busy:       # all cards have landed
            self.dealing = False
            # The clock does NOT start here: it starts with the player's
            # first move (see do_move and click_stock).
        # The clock only runs while a game is actually being played.
        if self.timer_on and not self.won and not self.win_pending:
            self.elapsed += dt
        # Wait for the last card to land before starting the celebration.
        if self.win_pending and not busy and not self.won:
            self.start_win()
        if self.won:
            self.update_win(dt)
        # Count down the short notice and the "click again to reset" window.
        if self.notice_time > 0:
            self.notice_time -= dt
        if self.reset_armed > 0:
            self.reset_armed -= dt
            if self.reset_armed <= 0:       # too slow: disarm the button again
                self.btn_reset.set_text("Reset Stats")

        # Update the status text only when it actually changes.
        # Rebuilding label text every frame is wasteful, so compare first.
        # (_mm_ss turns a number of seconds into text such as "1:15".)
        text = f"Moves: {self.moves}     Time: {_mm_ss(self.elapsed)}"
        if text != self.info.text:
            self.info.text = text
        # Wins / losses, plus the win percentage once a game has been played,
        # and the fastest win once there has been one.
        games = self.wins + self.losses
        pct = f"   ({round(100 * self.wins / games)}%)" if games else ""
        best = (f"   Fastest: {_mm_ss(self.best_time)}"
                if self.best_time is not None else "")
        stats = f"Wins: {self.wins}   Losses: {self.losses}{pct}{best}"
        if stats != self.stats_lbl.text:
            self.stats_lbl.text = stats

    # -- win celebration -----------------------------------------------------
    def start_win(self):
        """Begin the win celebration (called once the last card has landed)."""
        self.won = True
        self.stuck = False
        self.play("applause", long=True)
        self.win_time = 0.0
        self.win_idx = 0
        # Launch order: the four kings first, then the queens, ... down to
        # the aces (each foundation pile is A..K, so p[r - 1] has rank r).
        self.win_queue = [p[r - 1] for r in range(13, 0, -1) for p in self.found]

    def update_win(self, dt):
        """Cards are thrown off their foundations one by one and bounce
        under gravity until they leave the sides of the window."""
        # `s` makes speeds proportional to the card size, so the celebration
        # looks the same in a small window and a big one (112 px was the card
        # height the speeds were originally tuned for).
        s = self.ch / 112.0
        self.win_time += dt
        # Launch a new card every 0.14 seconds with a random velocity.
        while self.win_idx < len(self.win_queue) and self.win_time >= self.win_idx * 0.14:
            c = self.win_queue[self.win_idx]
            self.win_idx += 1
            c.animating = False
            c.launched = True
            c.z = next_z()
            c.vx = random.uniform(120, 420) * random.choice((-1, 1)) * s
            c.vy = random.uniform(150, 600) * s
        # Simple physics for every card launched so far: velocity changes
        # position, gravity changes velocity. (`win_queue[:n]` = the first n.)
        for c in self.win_queue[:self.win_idx]:
            if not c.launched:
                continue
            c.vy -= 1500 * s * dt           # gravity
            c.x += c.vx * dt
            c.y += c.vy * dt
            if c.y < 0:                     # bounce off the bottom edge
                c.y = 0
                c.vy = -c.vy * 0.78         # reverse direction, lose 22% speed
            if c.x < -self.cw * 1.2 or c.x > self.width + self.cw * 0.2:
                c.launched = False          # flew off-screen

    # -- drawing -----------------------------------------------------------
    def visible_cards(self):
        """The cards to draw this frame, in back-to-front order.

        Cards that are resting only need drawing if they can be seen (e.g.
        only the top two of the stock and foundations). Moving cards are
        drawn last, sorted by z, so they slide over everything else."""
        # `lst += other` appends all of `other`'s items to lst.
        base = []
        if self.stock:
            base += self.stock[-2:]         # only the top two are ever seen
        base += self.waste[-3:]             # the fanned cards
        # During the win celebration the cards are thrown off the foundations
        # one at a time. A card that has been thrown (win_queue[:win_idx]) no
        # longer belongs to its pile visually, even after it has flown off the
        # screen, so skip it here. Then the two cards left on top of each pile
        # are the ones drawn, and the piles shrink as cards leave instead of
        # vanishing. (Before the win `thrown` is empty, so this is just the
        # top two cards of each foundation.)
        thrown = set(self.win_queue[:self.win_idx])
        for p in self.found:
            base += [c for c in p if c not in thrown][-2:]
        for col in self.tab:
            base += col
        # Anything sliding, held by the mouse, or flying in the win animation
        # is "moving". sort(key=...) orders them by z, lowest first, so the
        # highest z ends up last in the list and is therefore drawn on top.
        moving = [c for c in self.cards if c.animating or c.dragging or c.launched]
        moving.sort(key=lambda c: c.z)
        # A set makes the "is this card in `moving`?" test fast, and stops a
        # moving card from being drawn twice (it is also in `base`).
        mset = set(moving)
        return [c for c in base if c not in mset] + moving

    def on_draw(self):
        """pyglet calls this whenever the window needs redrawing. Drawing
        order matters: things drawn later appear on top."""
        if not getattr(self, "_ready", False):
            return                          # still starting up: nothing to draw
        self.clear()                        # wipe the previous frame
        if self.bg_sprite:
            self.bg_sprite.draw()           # the background.png picture
        else:
            self.bg.draw()                  # plain green table
        self.top_bar.draw()                 # darker bar across the top
        for b in self.btns:
            b.draw()
        self.info.draw()
        self.stats_lbl.draw()
        for s in self.slots:
            s.draw()
        if not self.stock:                  # empty stock: show the recycle ring
            for r in self.ring:
                r.draw()
        for c in self.visible_cards():      # back-to-front, see visible_cards()
            c.draw()
        # Message banners go last so they appear over the cards.
        if self.won:
            self.win_shadow.draw()
            self.win_lbl.draw()
        elif self.stuck:
            self.stuck_shadow.draw()
            self.stuck_lbl.draw()
        elif self.notice_time > 0:          # the brief "moves are available" note
            self.notice_shadow.draw()
            self.notice_lbl.draw()
        self._loading_label = None          # the game is on screen: loading is over


if __name__ == "__main__":
    # argparse reads the command line and also provides -h / --help for free.
    # The resource folder is an optional positional argument; --refresh is a
    # flag (it is either given or not) and may appear anywhere.
    parser = argparse.ArgumentParser(description="Klondike Solitaire")
    parser.add_argument("resources", nargs="?",
                        help="the resource folder, which holds the card face "
                             "folders 'cards_1', 'cards_2', ..., a 'card-backs' "
                             "folder and a 'sounds' folder (default: a folder "
                             f"named '{RESOURCE_DIR}' next to this script)")
    parser.add_argument("--refresh", action="store_true",
                        help="rebuild the image cache even if it already exists")
    args = parser.parse_args()
    # Find the resource folder, then the card sets (cards_1, cards_2, ...), the
    # card backs and the sounds folder inside it. Either may be missing: the game then falls
    # back to drawn cards / no sound.
    resources = find_resource_dir(args.resources)
    Solitaire(find_card_sets(resources),
              resource_subdir(resources, SOUNDS_SUBDIR),
              refresh_cache=args.refresh,
              backs_dir=resource_subdir(resources, BACKS_SUBDIR),
              background=find_background(resources))
    pyglet.app.run()
