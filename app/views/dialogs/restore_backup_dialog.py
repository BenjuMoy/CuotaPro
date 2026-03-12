from datetime import datetime
from pathlib import Path
from tkinter import Listbox

import ttkbootstrap as ttk
from ttkbootstrap.dialogs.message import Messagebox

from app.services.application_service import ApplicationService


class RestoreBackupDialog:
    def __init__(self, parent: ttk.Window, service: ApplicationService):

        self.parent = parent
        self.service = service

        self.dialog = ttk.Toplevel(parent)
        self.dialog.title("Restaurar Respaldo")
        self.dialog.geometry("400x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self.backup_files: list[Path] = []

        self._build_ui()
        self._load_backups()

    # -------------------------
    # UI
    # -------------------------

    def _build_ui(self):

        ttk.Label(
            self.dialog,
            text="Seleccione un archivo de respaldo:",
        ).pack(pady=10)

        self.listbox = Listbox(self.dialog)
        self.listbox.pack(fill="both", expand=True, padx=10, pady=10)

        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(pady=10)

        ttk.Button(
            button_frame,
            text="Restaurar",
            bootstyle="danger",
            command=self._restore_selected,
        ).pack(side="left", padx=5)

        ttk.Button(
            button_frame,
            text="Cancelar",
            command=self.dialog.destroy,
        ).pack(side="left", padx=5)

    # -------------------------
    # Load Backups
    # -------------------------

    def _load_backups(self):

        self.backup_files = self.service.list_backup_files()

        for file in self.backup_files:
            # timestamp = file.stat().st_mtime
            timestamp = datetime.fromtimestamp(file.stat().st_mtime).strftime(
                "%Y-%m-%d %H:%M"
            )
            self.listbox.insert("end", f"{file.name} - {timestamp}")

    # -------------------------
    # Restore
    # -------------------------

    def _restore_selected(self):

        selection = self.listbox.curselection()

        if not selection:
            Messagebox.show_warning(
                "Seleccione un archivo de respaldo",
                "Advertencia",
            )
            return

        confirm = Messagebox.yesno(
            "Esto reemplazará la base de datos actual.\n\n"
            "Se recomienda crear un respaldo antes de continuar.\n\n"
            "¿Desea continuar?",
            "Confirmar Restauración",
        )

        if confirm != "Yes":
            return

        try:
            selected_file = self.backup_files[selection[0]]

            success = self.service.restore_backup(selected_file)

            if success:
                Messagebox.show_info(
                    "Respaldo restaurado correctamente",
                    "Éxito",
                )

                # Close application to reload DB
                self.parent.destroy()

            else:
                Messagebox.show_error(
                    "Error al restaurar respaldo",
                    "Error",
                )

        except Exception as e:
            Messagebox.show_error(
                f"Error al restaurar respaldo:\n{e}",
                "Error",
            )
