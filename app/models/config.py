from dataclasses import dataclass


@dataclass(frozen=True)
class AppConfig:
    window_title: str = "Cuota Pro"
    theme: str = "yeti"
