"""SCMC package."""

from .logic import MeritsCalculator
from .settings import SettingsManager

# Optional imports for customtkinter-based UI (if available)
_components_available = False
try:
    from .components import CalculatorSection, FeeSection, SettingsSection  # noqa: F401

    _components_available = True
except ImportError:
    # Qt UI doesn't require customtkinter components
    CalculatorSection = None  # type: ignore
    FeeSection = None  # type: ignore
    SettingsSection = None  # type: ignore

# Define __all__ based on what's available
__all__: list[str] = ["MeritsCalculator", "SettingsManager"]
if _components_available:
    __all__.extend(["CalculatorSection", "FeeSection", "SettingsSection"])
