from app.bootstrap.app_initializer import AppInitializer
from app.database.config import DatabaseConfig


def test_initializer_creates_services(tmp_path):
    db_path = tmp_path / "test.db"

    config = DatabaseConfig(db_path=db_path)
    initializer = AppInitializer(config)

    app_service = initializer.initialize()

    assert app_service is not None

    initializer.shutdown()
