# Quoridor — terminal edition

A complete, playable version of the board game **Quoridor** that runs in your terminal. Race your pawn across a 9×9 board and place walls to slow your opponents down — for 2 or 4 players, with a chess clock, a move counter and full-game replay.

```
     1   2   3   4   5   6   7   8   9
   ┌───┬───┬───┬───┬───┬───┬───┬───┬───┐
 1 │   │   │   │   │   │   │   │   │   │
   ├───┼───┼───┼───┼───┼───┼───┼───┼───┤
 2 │   │   │   │   │ A │   │   │   │   │
   ├───┼───┼───┼───┼───┼───┼───┼───┼───┤
 3 │   │   │   │   │   │   │   │   │   │
   ├───┼───┼───┼═══════┼───┼───┼───┼───┤
 4 │   │   │   │   │   │   │   │   │   │
   ├───┼───┼───┼───┼───┼───┼───┼───┼───┤
 5 │   │   │   │   │   │   │   │   │   │
   ├───┼───┼───┼───┼───┼───┼───┼───┼───┤
 6 │   │   │   │   │   │   │   │   │   │
   ├───┼───┼───┼───┼───┼───┼───┼───┼───┤
 7 │   │   │   │   │   │   │   │   │   │
   ├───┼───┼───┼───┼───┼───┼───┼───┼───┤
 8 │   │   │   │   │   │   │   │   │   │
   ├───┼───┼───┼───┼───┼───┼───┼───┼───┤
 9 │   │   │   │   │ B │   │   │   │   │
   └───┴───┴───┴───┴───┴───┴───┴───┴───┘
Clocks: A 4:56   B 4:52
Player A's turn (top -> bottom)  Turn 2 | Walls left: 10 | Distance to goal: 8
```

*The double line under row 3 is a wall, placed with `h 3 4`. Horizontal walls are drawn with `═` and vertical walls with `║`.*

## Features

- **2 or 4 players**, taking turns clockwise.
- **Chess clock** — every player has a time bank that only runs on their turn. Run out of time and you're out of the game.
- **Move counter and end-of-game summary** — turns, steps, walls placed, walls left and time used for each player.
- **Full-game replay** — every game is recorded; watch it back step by step or on autoplay, and save it to a file to replay later.
- **The "no trapping" rule** — a wall is refused if it would leave *any* player with no route to their goal edge, found with a breadth-first search. You can never wall someone into a pocket they can't escape (or wall yourself in).
- **Distance to goal** shown on every turn, so you can see what a wall is really costing your opponent.
- **Friendly input handling** — typos and illegal moves get a clear message and another try; they never crash the game.
- Pure Python standard library: no extra packages to install.

## Quick start: play in 5 steps

No programming experience needed. These steps work on Windows, Mac and Linux.

### Step 1: Make sure Python is installed

You need **Python 3.9 or newer**. To check, open a terminal (see Step 3) and type:

```
python --version
```

- If it shows `Python 3.9` or higher, you're ready.
- If it says Python isn't recognised or found, try `py --version` (Windows) or `python3 --version` (Mac and Linux). Whichever works is the command to use in Step 4.
- If none of them work, download Python from [python.org/downloads](https://www.python.org/downloads/). **On Windows, tick "Add python.exe to PATH" on the first installer screen**, then close and reopen your terminal.

### Step 2: Download the game

1. At the top of this page, click the green **Code** button.
2. Click **Download ZIP**.
3. Find the downloaded file (usually in your Downloads folder) and **extract it**:
   - **Windows:** right-click the zip and choose **Extract All…**
   - **Mac:** double-click the zip.
   - **Linux:** run `unzip quoridor-terminal-main.zip`.

You'll get a folder called `quoridor-terminal-main`. Open it. If you only see one more folder inside, open that too, until you can see `main.py` and `README.md` side by side.

### Step 3: Open a terminal in that folder

- **Windows:** with the folder open in File Explorer, click the address bar at the top, type `cmd` and press Enter. A black window opens, already in the right place.
- **Mac:** open **Terminal** (press Cmd+Space, type "Terminal", press Enter). Type `cd ` (with a space after it), drag the folder from Finder into the Terminal window, and press Enter.
- **Linux:** right-click inside the folder and choose **Open in Terminal**.

### Step 4: Start the game

Type this and press Enter:

```
python main.py
```

Use `py main.py` or `python3 main.py` instead if that was the command that worked in Step 1. You should see:

```
How many players? (2 or 4):
```

### Step 5: Play

1. Type `2` (or `4`) and press Enter.
2. Press Enter to accept the default 5 minutes per player. Type `0` for no clock, or any number of minutes.
3. The board appears. On your turn, type a number and press Enter:
   - `1` up, `2` down, `3` left, `4` right
   - `5` to place a wall (for example `h 3 4`, explained below)
   - `q` to quit
4. Players take turns until someone reaches the opposite edge. A summary of the game appears, and you can save it and watch the replay.

> **Prefer git?**
> ```bash
> git clone https://github.com/ridhimasinghal19/quoridor-terminal.git
> cd quoridor-terminal
> python main.py
> ```

You can also skip the questions with command-line options:

```bash
python main.py --players 4 --minutes 10
python main.py --players 2 --minutes 0      # no clock
```

## How to play

Reach the opposite edge of the board before anyone else does.

| Player | Starts at | Goal |
| ------ | --------- | ---- |
| A | top | bottom edge |
| B | right (4 players) / bottom (2 players) | left (4 players) / top (2 players) |
| C | bottom (4 players only) | top edge |
| D | left (4 players only) | right edge |

On your turn, enter a number:

| Key | Action |
| --- | ------ |
| `1` `2` `3` `4` | Move one cell up, down, left or right |
| `5` | Place a wall |
| `q` | Quit the game |

You can't move off the board, through a wall, or onto another pawn. Each player starts with **10 walls** in a 2-player game and **5 walls** in a 4-player game.

### Placing walls

A wall is two cells long. Name it with its orientation and the row and column (1–8) of its **anchor cell**:

```
h 3 5   a horizontal wall directly below cell (3, 5) and the cell to its right
v 3 5   a vertical wall directly right of cell (3, 5) and the cell below it
```

Walls can't overlap or cross each other, but they can meet end to end, at a corner or in a T shape. Horizontal walls are drawn with `═`, vertical walls with `║`. Type `b` at the wall prompt to go back and choose a different action.

### The clock

Each player has their own time bank, which counts down only during their turn. The clock is checked whenever you press Enter, so a turn that runs over the limit is caught as soon as you submit it — the late move doesn't count, and you leave the game. In a 2-player game your opponent wins; in a 4-player game play continues without you.

### Replays

When a game ends you can save it and watch it back:

```
Save this game to a file? Type a file name, or press Enter to skip: my_game
Saved to my_game.json. Replay it any time with: python main.py --replay my_game.json
Watch the replay? [s]tep through, [a]utoplay, or Enter to skip:
```

To replay a saved game later:

```bash
python main.py --replay my_game.json              # autoplay, one turn per second
python main.py --replay my_game.json --delay 0.3  # faster
python main.py --replay my_game.json --step       # press Enter for each turn
```

Saved games are plain JSON, so they're easy to inspect.

### End-of-game summary

```
============== GAME OVER ==============
Player A wins by reaching the bottom edge after 9 turns (9 steps and 0 walls placed).

Player  Turns  Steps  Walls placed  Walls left  Time used
------  -----  -----  ------------  ----------  ---------
A       9      9      0             10          0:40
B       8      7      1             9           0:36

Total turns: 17   Game time: 1:16
```

### Rules in this version

- Pawns can't jump over each other. If a pawn blocks you, go around it.
- If a player has no legal move and no walls left, their turn is skipped. If nobody can act, the game is a draw.

## Project layout

```
quoridor-terminal/
├── main.py              # entry point: python main.py
├── quoridor/
│   ├── models.py        # directions, walls, player layout
│   ├── pathfinding.py   # wall-aware movement and breadth-first search
│   ├── board.py         # game state, move and wall rules, board drawing
│   ├── clock.py         # chess clock
│   ├── history.py       # game record, JSON save and load
│   ├── replay.py        # step-by-step replay
│   ├── report.py        # end-of-game statistics
│   ├── game.py          # turn loop and prompts
│   └── cli.py           # command-line options
└── tests/               # 62 unit tests
```

The rules live in `board.py` and know nothing about the terminal, so the engine could be reused with a different interface.

## Running the tests

In the same folder as `main.py`, run:

```bash
python -m unittest
```

You should see `Ran 62 tests` followed by `OK`. If you have pytest installed, `pytest` works too.

## Credits

Quoridor is a board game designed by Mirko Marchesi and published by Gigamic. This is an independent, unofficial implementation written for fun and practice.

## License

[MIT](LICENSE)
