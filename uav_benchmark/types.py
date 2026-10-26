from dataclasses import asdict, dataclass
from typing import Optional


@dataclass(frozen=True)
class Sample:
    time: float
    position: tuple[float, float, float]
    velocity: tuple[float, float, float]
    collision: bool = False
    reached_goal: bool = False


@dataclass(frozen=True)
class RunConfig:
    target_speed_mps: float = 2.0
    timeout_s: float = 12.0
    dt_s: float = 1 / 15
    goal_radius_m: float = 0.5
    ground_z_m: float = -1.0
    collision_tolerance_m: float = 1e-8
    traversability_grid: int = 5
    traversability_headings: int = 8
    traversability_step_m: float = 0.1

    def to_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class MetricResult:
    value: Optional[float]
    unit: str
    status: str = "ok"
    note: str = ""
    version: str = "1.0"

    def to_dict(self):
        return asdict(self)
