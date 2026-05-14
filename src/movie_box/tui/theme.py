from dataclasses import dataclass


@dataclass(frozen=True)
class CyberpunkTheme:
    background: str = "#000000"
    surface: str = "#09090b"
    surface_lift: str = "#18181b"
    text: str = "#f5f3ff"
    muted: str = "#8b8795"
    dim: str = "#575268"
    neon: str = "#d946ef"
    neon_hot: str = "#ff7aff"
    neon_soft: str = "#c084fc"
    violet: str = "#8b5cf6"
    blue: str = "#38bdf8"
    success: str = "#22c55e"
    warning: str = "#facc15"
    danger: str = "#fb7185"

    @property
    def gradient(self) -> tuple[str, ...]:
        return (
            f"bold {self.neon_hot}",
            f"bold {self.neon}",
            f"bold {self.neon_soft}",
            f"bold {self.violet}",
            f"bold {self.blue}",
        )


THEME = CyberpunkTheme()

