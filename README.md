# Outil de conversion de bases

A desktop number-base converter built with **Python + Tkinter**.  
The interface is fully in **French**, features a pastel colour scheme, and auto-saves every successful conversion to a scrollable history table.

---

## Features

| Feature | Detail |
|---|---|
| Live conversion | Result updates as you type — no button press needed |
| Auto-save to history | Every valid conversion is instantly appended to the history table |
| Four bases supported | Binary (2), Octal (8), Decimal (10), Hexadecimal (16) |
| Two's complement for binary | Negative binary numbers use two's complement representation |
| Export history | Save the full history as a formatted `.json` file |
| French UI | Every label, heading, button and status message is in French |
| Pastel colour scheme | Clear Inputs → pastel red · Base dropdowns → pastel blue · Export → pastel green |

---

## Requirements

- Python 3.9 or later  
- `tkinter` (included in the standard library for macOS / Windows / most Linux distros)

No third-party packages are required.

---

## Running the App

```bash
python3 app.py
```

The window opens at **980 × 620 px** and adapts the `clam` theme when it is available.

---

## Project Structure

```
Calculator/
├── app.py      # Single-file application — all logic and UI here
└── README.md   # This file
```

---

## Code Walkthrough

### 1. Data Model — `ConversionRecord`

```python
@dataclass
class ConversionRecord:
    timestamp: str
    original_number: str
    source_base: int
    target_base: int
    result_value: str

    def as_dict(self) -> dict:
        return { ... }   # used when exporting to JSON
```

Every successful conversion is wrapped in a `ConversionRecord` dataclass.  
The `as_dict()` method serialises the record so it can be written to a JSON file via `json.dump()`.

---

### 2. Application Class — `BaseCalculatorApp`

The entire app lives in one class.  `__init__` wires together three things:

```python
def __init__(self, root: Tk) -> None:
    # 1. Tkinter StringVars shared between the model and the view
    self.input_var        = StringVar()
    self.source_base_var  = StringVar(value="Decimal (10)")
    self.target_base_var  = StringVar(value="Binary (2)")
    self.result_var       = StringVar(value="")
    self.status_var       = StringVar(value="Entrez un nombre à convertir.")

    # 2. In-memory history list
    self.history: list[ConversionRecord] = []

    # 3. Build the UI, bind events, run one conversion to initialise
    self._build_ui()
    self._bind_events()
    self.update_result()
```

---

### 3. UI Construction — `_build_ui()`

#### Pastel Colour Palette

The colours are defined as local constants at the top of `_build_ui()`:

```python
PASTEL_BLUE   = "#a8c8f0"
PASTEL_RED    = "#f4a7a7"
PASTEL_GREEN  = "#a8e6b4"
BTN_FG        = "#1a1a1a"
BTN_ACTIVE_BG = "#d0d0d0"
```

Because `ttk` widgets do not accept a plain `bg=` colour argument, two different widget types are used:

| Widget | How colour is applied |
|---|---|
| `ttk.Combobox` | A custom `ttk.Style` named `"Blue.TCombobox"` is registered and applied via `style="Blue.TCombobox"` |
| `tk.Button` (Clear Inputs, Export JSON) | Plain `tk.Button` accepts `bg=`, `fg=`, `activebackground=` directly |

```python
# Register the blue combobox style once
style = ttk.Style()
style.configure("Blue.TCombobox",
                fieldbackground=PASTEL_BLUE,
                background=PASTEL_BLUE,
                selectbackground=PASTEL_BLUE,
                selectforeground=BTN_FG)

# Apply it to both dropdowns
src_combo = ttk.Combobox(..., style="Blue.TCombobox")
dst_combo = ttk.Combobox(..., style="Blue.TCombobox")

# Pastel-red tk.Button for "Effacer la saisie"
tk.Button(button_row,
          text="Effacer la saisie",
          bg=PASTEL_RED, fg=BTN_FG,
          activebackground=BTN_ACTIVE_BG,
          relief="flat", padx=10, pady=4, cursor="hand2",
          command=self.clear_inputs).pack(side="left", padx=(0, 8))

# Pastel-green tk.Button for "Exporter l'historique (en JSON)"
tk.Button(history_actions,
          text="Exporter l'historique (en JSON)",
          bg=PASTEL_GREEN, fg=BTN_FG,
          activebackground=BTN_ACTIVE_BG,
          relief="flat", padx=10, pady=4, cursor="hand2",
          command=self.export_history_json).pack(side="left", padx=(0, 8))
```

#### Layout

The UI uses a two-section vertical layout:

```
┌──────────────────────────────────────────────────────────┐
│  Outil de conversion de bases  (LabelFrame)              │
│                                                          │
│  Nombre d'origine │ Base source │ Base cible │ Résultat  │
│  [entry]          │ [combobox]  │ [combobox] │ [readonly]│
│                                                          │
│  [ Effacer la saisie ]                                   │
│  Status message…                                         │
└──────────────────────────────────────────────────────────┘
┌──────────────────────────────────────────────────────────┐
│  Historique  (LabelFrame)                                │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ Date & Heure │ Nombre d'origine │ Base source │ … │ │ │
│  │ …            │ …               │ …           │ … │ │ │
│  └─────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
  [ Vider l'historique ]  [ Exporter l'historique (en JSON) ]
```

The top section uses a `grid` layout (4 columns, `columnconfigure` with weight=2 for the text fields and weight=1 for the dropdowns). The history section uses `pack` with a vertical `ttk.Scrollbar` attached to the `Treeview`.

---

### 4. Live Conversion + Auto-Save — `update_result()`

Tkinter `StringVar.trace_add("write", ...)` triggers `update_result()` on every keystroke and every dropdown change:

```python
def _bind_events(self) -> None:
    self.input_var.trace_add("write", lambda *_: self.update_result())
    self.source_base_var.trace_add("write", lambda *_: self.update_result())
    self.target_base_var.trace_add("write", lambda *_: self.update_result())
```

Inside `update_result()`, a successful parse+format immediately appends a `ConversionRecord` to both `self.history` and the on-screen `Treeview`:

```python
def update_result(self) -> None:
    raw_text = self.input_var.get()
    src_base = self.selected_base(self.source_base_var.get())
    dst_base = self.selected_base(self.target_base_var.get())

    if not raw_text.strip():
        self.result_var.set("")
        self.status_var.set("Entrez un nombre à convertir.")
        return

    try:
        value     = self.parse_input_value(raw_text, src_base)
        converted = self.format_output_value(value, dst_base)
        self.result_var.set(converted)

        # ── Auto-save ──────────────────────────────────────────
        record = ConversionRecord(
            timestamp      = datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            original_number= raw_text,
            source_base    = src_base,
            target_base    = dst_base,
            result_value   = converted,
        )
        self.history.append(record)
        self.tree.insert("", "end", values=(
            record.timestamp, record.original_number,
            record.source_base, record.target_base, record.result_value,
        ))
        self.status_var.set("Conversion effectuée — enregistrée dans l'historique.")
        # ───────────────────────────────────────────────────────

    except ValueError as exc:
        self.result_var.set("")
        self.status_var.set(str(exc))
```

---

### 5. Number Parsing — `parse_input_value()`

```python
def parse_input_value(self, raw_text: str, base: int) -> int:
```

| Base | Validation | Negative representation |
|---|---|---|
| 2 (Binary) | Only `0` and `1` allowed; `-` sign rejected | Two's complement (leading `1` bit) |
| 8 (Octal) | Digits `0–7` only | Explicit `-` prefix |
| 10 (Decimal) | Digits `0–9` only | Explicit `-` prefix |
| 16 (Hex) | Digits `0–9`, letters `A–F` (case-insensitive) | Explicit `-` prefix |

Two's complement parsing for binary:

```python
value = int(text, 2)
if text[0] == "1":          # leading 1 → negative in two's complement
    value -= 1 << len(text)
```

---

### 6. Number Formatting — `format_output_value()`

```python
def format_output_value(self, value: int, target_base: int) -> str:
```

| Target base | Output format |
|---|---|
| 10 | `str(value)` |
| 8 | `format(abs(value), "o")` with optional `-` prefix |
| 16 | `format(abs(value), "X")` with optional `-` prefix |
| 2 | Positive → `format(value, "b")` · Negative → minimal-width two's complement |

Two's complement output for binary negatives:

```python
width = 1
while value < -(1 << (width - 1)):
    width += 1
twos_comp = (1 << width) + value
return format(twos_comp, f"0{width}b")
```

---

### 7. JSON Export — `export_history_json()`

Opens a native save-file dialog (`filedialog.asksaveasfilename`) and writes all records using `json.dump`:

```python
payload = [record.as_dict() for record in self.history]
with open(path, "w", encoding="utf-8") as f:
    json.dump(payload, f, indent=2)
```

**Example output:**

```json
[
  {
    "timestamp": "2026-03-02 22:05:00",
    "original_number": "1010",
    "source_base": 2,
    "target_base": 10,
    "result_value": "10"
  }
]
```

---

### 8. Entry Point

```python
def main() -> None:
    root = Tk()
    style = ttk.Style()
    if "clam" in style.theme_names():
        style.theme_use("clam")   # modern flat look where available
    BaseCalculatorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
```

---

## UI Changes Summary (vs. original version)

| What changed | Detail |
|---|---|
| Removed **Save to History** button | Saving is now automatic on every valid conversion |
| Removed **Explore JSON** button | — |
| Removed **Delete Selected** button | — |
| Removed binary hint label | The two's complement note below the input row was removed |
| Added pastel colours | Red / Blue / Green palette applied to buttons and dropdowns |
| French localisation | All labels, headings, buttons and status/dialog strings translated |

---

## Licence

MIT — feel free to use, fork and modify.
