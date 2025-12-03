"""MeritsCalc package."""

from .components import CalculatorSection, FeeSection, SettingsSection
from .logic import MeritsCalculator
from .settings import SettingsManager

__all__: list[str] = [
    "MeritsCalculator",
    "SettingsManager",
    "CalculatorSection",
    "FeeSection",
    "SettingsSection",
]
