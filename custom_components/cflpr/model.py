from dataclasses import dataclass


@dataclass
class PRItem:
    id: str
    name: str


@dataclass
class PRAvailability:
    fill_rate: float
    free_spaces: int
    free_electric_spaces: int
    free_pmr_spaces: int
