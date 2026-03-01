# Calculator for Bases (Desktop, Python)

This is a desktop base-conversion app built with Tkinter.

## Features
- Convert instantly between base 2, 8, 10, and 16.
- Supports negative numbers:
  - Base 2 uses two's complement interpretation for negatives.
  - Base 8/10/16 use an explicit `-` sign.
- Save conversions to history with date/time.
- Delete selected history rows.
- Clear full history.
- Export history to JSON.
- Explore history as JSON inside the app.

## Run
```bash
python3 app.py
```

## Notes
- For binary input, do not type `-` for negatives.
- Example: `1011` (4-bit two's complement) is interpreted as `-5`.
- For positive values in binary with leading `1`, add a leading `0` bit if needed.
  - Example: use `01010` for positive decimal `10`.
