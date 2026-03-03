import os
import shutil
from pathlib import Path

from app.database.config import DatabaseConfig
from app.utils.helpers import fecha_actual


class DatabaseMaintenance:
    def __init__(self, db_config: DatabaseConfig) -> None:
        self.db_config = db_config

    def create_backup(self, db_config):
        if not os.path.exists(db_config.db_dir):
            os.mkdir(db_config.db_dir)

        if not os.path.exists(db_config.db_path):
            with open(db_config.db_path, "x") as f:
                f.write("")

        if not os.path.exists(db_config.backup_dir):
            os.mkdir(db_config.backup_dir)

        backup_path = Path(
            str(db_config.backup_dir)
            + "/"
            + "student_manager_backup_"
            + fecha_actual()
            + ".db"
        )
        try:
            shutil.copyfile(db_config.db_path, backup_path)
            print("db backed up succesfully")
        except Exception as e:
            raise e

    def restore_backup(self, file_to_restore):
        try:
            shutil.copyfile(file_to_restore, self.db_config.db_path)
            print("db backed up succesfully")
        except Exception as e:
            raise e
