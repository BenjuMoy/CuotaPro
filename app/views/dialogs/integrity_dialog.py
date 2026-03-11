import ttkbootstrap as ttk
from ttkbootstrap.dialogs.message import Messagebox

from app.services.application_service import ApplicationService


def verify_integrity(main_service: ApplicationService):
    """Verify the integrity of the database."""
    try:
        status = main_service.verify_integrity()
        if status:
            Messagebox.show_info(
                "La base de datos está íntegra", "Verificación Completada"
            )
            self.update_status("Verificación de integridad completada")
        else:
            Messagebox.show_warning(
                "La base de datos tiene problemas de integridad", "Advertencia"
            )
            self.update_status("Problemas de integridad detectados")
    except Exception as e:
        Messagebox.show_error(f"Error al verificar integridad: {e}", "Error")
