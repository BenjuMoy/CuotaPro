from tkinter import Listbox

import ttkbootstrap as ttk
from ttkbootstrap.dialogs.message import Messagebox

from app.services.application_service import ApplicationService


def restore_selected(
    parent,
    main_service: ApplicationService,
    listbox: Listbox,
) -> bool:
    try:
        confirm = Messagebox.yesno(
            "Esto reemplazará la base de datos actual.\n\n"
            "Se recomienda crear un respaldo antes de continuar.\n\n"
            "¿Desea continuar?",
            "Confirmar Restauración",
        )
        if confirm != "Yes":
            return False

        selection = listbox.curselection()
        if not selection:
            Messagebox.show_warning("Seleccione un archivo de respaldo", "Advertencia")
            return False

        selected_file = backup_files[selection[0]]
        if main_service.restore_backup(str(selected_file)):
            Messagebox.show_info("Respaldo restaurado correctamente", "Éxito")
            # self.update_status("Respaldo restaurado")
            # Restart the application to reload the data
            parent.destroy()
            # self.root.event_generate("<<RestartApp>>")
            return True
        else:
            Messagebox.show_error("Error al restaurar respaldo", "Error")
            self.dialog.destroy()
            return False
    except Exception as e:
        Messagebox.show_error(f"Error al restaurar respaldo: {e}", "Error")
        return False


class RestoreBackupDialog:
    def __init__(self, parent: ttk.Window, service: ApplicationService):
        self.parent = parent
        self.main_service = service
        self.dialog = ttk.Toplevel(parent)

        return self._build_ui()

    def _build_ui(self) -> bool:
        self.dialog.title("Restaurar Respaldo")
        self.dialog.geometry("400x300")
        self.dialog.transient(self.root)
        self.dialog.grab_set()

        ttk.Label(self.dialog, text="Seleccione un archivo de respaldo:").pack(pady=10)

        # List available backup files
        backup_files = self.main_service.list_backup_files()

        self.listbox = Listbox(self.dialog)
        self.listbox.pack(fill="both", expand=True, padx=10, pady=10)

        for backup_file in backup_files:
            self.listbox.insert(
                "end", f"{backup_file.name} - {backup_file.stat().st_mtime}"
            )

        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(pady=10)

        self.res: bool

        ttk.Button(
            button_frame,
            text="Restaurar",
            command=self.aux_func,
        ).pack(side="left", padx=5)

        ttk.Button(button_frame, text="Cancelar", command=self.dialog.destroy).pack(
            side="left", padx=5
        )

        return self.res

    def aux_func(self):

        self.res = restore_selected(self.parent, self.main_service, self.listbox)
