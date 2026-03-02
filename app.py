import json
import tkinter as tk
from dataclasses import dataclass
from datetime import datetime
from tkinter import Tk, StringVar, filedialog, messagebox
from tkinter import ttk

SUPPORTED_BASES = (2, 8, 10, 16)
BASE_LABELS = {
    "Binary (2)": 2,
    "Octal (8)": 8,
    "Decimal (10)": 10,
    "Hexadecimal (16)": 16,
}


@dataclass
class ConversionRecord:
    timestamp: str
    original_number: str
    source_base: int
    target_base: int
    result_value: str

    def as_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "original_number": self.original_number,
            "source_base": self.source_base,
            "target_base": self.target_base,
            "result_value": self.result_value,
        }


class BaseCalculatorApp:
    def __init__(self, root: Tk) -> None:
        self.root = root
        self.root.title("Outil de conversion de bases")
        self.root.geometry("980x620")

        self.input_var = StringVar()
        self.source_base_var = StringVar(value="Decimal (10)")
        self.target_base_var = StringVar(value="Binary (2)")
        self.result_var = StringVar(value="")
        self.status_var = StringVar(value="Entrez un nombre à convertir.")

        self.history: list[ConversionRecord] = []

        self._build_ui()
        self._bind_events()
        self.update_result()

    def _build_ui(self) -> None:
        main = ttk.Frame(self.root, padding=14)
        main.pack(fill="both", expand=True)

        # ── Pastel colour palette ──
        PASTEL_BLUE   = "#a8c8f0"
        PASTEL_RED    = "#f4a7a7"
        PASTEL_GREEN  = "#a8e6b4"
        BTN_FG        = "#1a1a1a"
        BTN_ACTIVE_BG = "#d0d0d0"

        # Style for readonly comboboxes (pastel blue)
        style = ttk.Style()
        style.configure("Blue.TCombobox",
                        fieldbackground=PASTEL_BLUE,
                        background=PASTEL_BLUE,
                        selectbackground=PASTEL_BLUE,
                        selectforeground=BTN_FG)

        input_box = ttk.LabelFrame(main, text="Outil de conversion de bases", padding=12)
        input_box.pack(fill="x", pady=(0, 10))

        ttk.Label(input_box, text="Nombre d'origine").grid(row=0, column=0, sticky="w")
        entry = ttk.Entry(input_box, textvariable=self.input_var, width=42)
        entry.grid(row=1, column=0, padx=(0, 12), sticky="ew")
        entry.focus_set()

        ttk.Label(input_box, text="Base source").grid(row=0, column=1, sticky="w")
        src_combo = ttk.Combobox(
            input_box,
            textvariable=self.source_base_var,
            values=list(BASE_LABELS.keys()),
            state="readonly",
            width=18,
            style="Blue.TCombobox",
        )
        src_combo.grid(row=1, column=1, padx=(0, 12), sticky="ew")

        ttk.Label(input_box, text="Base cible").grid(row=0, column=2, sticky="w")
        dst_combo = ttk.Combobox(
            input_box,
            textvariable=self.target_base_var,
            values=list(BASE_LABELS.keys()),
            state="readonly",
            width=18,
            style="Blue.TCombobox",
        )
        dst_combo.grid(row=1, column=2, padx=(0, 12), sticky="ew")

        ttk.Label(input_box, text="Résultat converti").grid(row=0, column=3, sticky="w")
        ttk.Entry(input_box, textvariable=self.result_var, state="readonly", width=35).grid(
            row=1, column=3, sticky="ew"
        )

        button_row = ttk.Frame(input_box)
        button_row.grid(row=2, column=0, columnspan=4, sticky="w", pady=(10, 0))

        # Pastel-red "Clear Inputs" button
        tk.Button(
            button_row,
            text="Effacer la saisie",
            command=self.clear_inputs,
            bg=PASTEL_RED,
            fg=BTN_FG,
            activebackground=BTN_ACTIVE_BG,
            relief="flat",
            padx=10,
            pady=4,
            cursor="hand2",
        ).pack(side="left", padx=(0, 8))

        ttk.Label(input_box, textvariable=self.status_var, foreground="#7a0000").grid(
            row=3, column=0, columnspan=4, sticky="w", pady=(6, 0)
        )

        input_box.columnconfigure(0, weight=2)
        input_box.columnconfigure(1, weight=1)
        input_box.columnconfigure(2, weight=1)
        input_box.columnconfigure(3, weight=2)

        history_box = ttk.LabelFrame(main, text="Historique", padding=10)
        history_box.pack(fill="both", expand=True)

        columns = ("timestamp", "original", "source", "target", "result")
        self.tree = ttk.Treeview(history_box, columns=columns, show="headings", height=13)
        self.tree.heading("timestamp", text="Date & Heure")
        self.tree.heading("original", text="Nombre d'origine")
        self.tree.heading("source", text="Base source")
        self.tree.heading("target", text="Base cible")
        self.tree.heading("result", text="Résultat converti")

        self.tree.column("timestamp", width=170, anchor="w")
        self.tree.column("original", width=180, anchor="w")
        self.tree.column("source", width=100, anchor="center")
        self.tree.column("target", width=100, anchor="center")
        self.tree.column("result", width=220, anchor="w")

        self.tree.pack(fill="both", expand=True, side="left")
        scrollbar = ttk.Scrollbar(history_box, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(fill="y", side="right")

        history_actions = ttk.Frame(main)
        history_actions.pack(fill="x", pady=(8, 0))

        ttk.Button(history_actions, text="Vider l'historique", command=self.clear_history).pack(
            side="left", padx=(0, 8)
        )
        # Pastel-green "Export JSON" button
        tk.Button(
            history_actions,
            text="Exporter l'historique (en JSON)",
            command=self.export_history_json,
            bg=PASTEL_GREEN,
            fg=BTN_FG,
            activebackground=BTN_ACTIVE_BG,
            relief="flat",
            padx=10,
            pady=4,
            cursor="hand2",
        ).pack(side="left", padx=(0, 8))

    def _bind_events(self) -> None:
        self.input_var.trace_add("write", lambda *_: self.update_result())
        self.source_base_var.trace_add("write", lambda *_: self.update_result())
        self.target_base_var.trace_add("write", lambda *_: self.update_result())

    def selected_base(self, selected_label: str) -> int:
        return BASE_LABELS[selected_label]

    def parse_input_value(self, raw_text: str, base: int) -> int:
        text = raw_text.strip()
        if not text:
            raise ValueError("Input is empty.")

        if base == 2:
            if text.startswith("-"):
                raise ValueError("Binary negatives must be entered using two's complement bits, not '-' sign.")
            if any(ch not in "01" for ch in text):
                raise ValueError("Binary input must use only 0 and 1.")

            value = int(text, 2)
            # Two's complement interpretation for negatives.
            if text[0] == "1" and len(text) > 0:
                value -= 1 << len(text)
            return value

        sign = -1 if text.startswith("-") else 1
        number_text = text[1:] if sign == -1 else text

        if not number_text:
            raise ValueError("No digits after sign.")

        if base == 8 and any(ch not in "01234567" for ch in number_text):
            raise ValueError("Octal input must use digits 0-7.")
        if base == 10 and not number_text.isdigit():
            raise ValueError("Decimal input must use digits 0-9.")
        if base == 16 and any(ch.upper() not in "0123456789ABCDEF" for ch in number_text):
            raise ValueError("Hex input must use digits 0-9 or A-F.")

        return sign * int(number_text, base)

    def format_output_value(self, value: int, target_base: int) -> str:
        if target_base == 10:
            return str(value)

        if target_base == 8:
            abs_digits = format(abs(value), "o")
            return f"-{abs_digits}" if value < 0 else abs_digits

        if target_base == 16:
            abs_digits = format(abs(value), "X")
            return f"-{abs_digits}" if value < 0 else abs_digits

        if target_base == 2:
            if value >= 0:
                return format(value, "b")

            width = 1
            while value < -(1 << (width - 1)):
                width += 1
            twos_comp = (1 << width) + value
            return format(twos_comp, f"0{width}b")

        raise ValueError("Unsupported target base.")

    def update_result(self) -> None:
        raw_text = self.input_var.get()
        src_base = self.selected_base(self.source_base_var.get())
        dst_base = self.selected_base(self.target_base_var.get())

        if not raw_text.strip():
            self.result_var.set("")
            self.status_var.set("Entrez un nombre à convertir.")
            return

        try:
            value = self.parse_input_value(raw_text, src_base)
            converted = self.format_output_value(value, dst_base)
            self.result_var.set(converted)
            # Auto-save every successful conversion
            record = ConversionRecord(
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                original_number=raw_text,
                source_base=src_base,
                target_base=dst_base,
                result_value=converted,
            )
            self.history.append(record)
            self.tree.insert(
                "",
                "end",
                values=(
                    record.timestamp,
                    record.original_number,
                    record.source_base,
                    record.target_base,
                    record.result_value,
                ),
            )
            self.status_var.set("Conversion effectuée — enregistrée dans l'historique.")
        except ValueError as exc:
            self.result_var.set("")
            self.status_var.set(str(exc))

    def save_current_conversion(self) -> None:
        raw_text = self.input_var.get().strip()
        src_base = self.selected_base(self.source_base_var.get())
        dst_base = self.selected_base(self.target_base_var.get())

        if not raw_text:
            messagebox.showerror("Cannot Save", "Enter a number first.")
            return

        try:
            value = self.parse_input_value(raw_text, src_base)
            converted = self.format_output_value(value, dst_base)
        except ValueError as exc:
            messagebox.showerror("Cannot Save", str(exc))
            return

        record = ConversionRecord(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            original_number=raw_text,
            source_base=src_base,
            target_base=dst_base,
            result_value=converted,
        )
        self.history.append(record)
        self.tree.insert(
            "",
            "end",
            values=(
                record.timestamp,
                record.original_number,
                record.source_base,
                record.target_base,
                record.result_value,
            ),
        )
        self.status_var.set("Saved to history.")

    def clear_inputs(self) -> None:
        self.input_var.set("")
        self.result_var.set("")
        self.status_var.set("Saisie effacée.")

    def delete_selected_history(self) -> None:
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("History", "Select at least one row to delete.")
            return

        indexes = sorted((self.tree.index(item_id) for item_id in selected), reverse=True)
        for item_id in selected:
            self.tree.delete(item_id)
        for idx in indexes:
            if 0 <= idx < len(self.history):
                del self.history[idx]

        self.status_var.set("Selected history entries deleted.")

    def clear_history(self) -> None:
        if not self.history:
            return

        if not messagebox.askyesno("Vider l'historique", "Supprimer toutes les entrées de l'historique ?"):
            return

        self.history.clear()
        for item_id in self.tree.get_children():
            self.tree.delete(item_id)

        self.status_var.set("Historique vidé.")

    def export_history_json(self) -> None:
        if not self.history:
            messagebox.showinfo("Exporter", "Aucun historique disponible à exporter.")
            return

        path = filedialog.asksaveasfilename(
            title="Exporter l'historique en JSON",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            initialfile="conversion_history.json",
        )
        if not path:
            return

        payload = [record.as_dict() for record in self.history]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        self.status_var.set(f"Historique exporté vers {path}")

    def explore_history_json(self) -> None:
        preview = Toplevel(self.root)
        preview.title("History JSON Explorer")
        preview.geometry("780x480")

        text = Text(preview, wrap="none")
        text.pack(fill="both", expand=True)

        payload = [record.as_dict() for record in self.history]
        text.insert("1.0", json.dumps(payload, indent=2))
        text.configure(state="disabled")


def main() -> None:
    root = Tk()
    # Use a modern native theme when available.
    style = ttk.Style()
    if "clam" in style.theme_names():
        style.theme_use("clam")
    BaseCalculatorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
