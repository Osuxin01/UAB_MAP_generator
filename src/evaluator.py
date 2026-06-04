from dataclasses import dataclass
from math import hypot

import numpy as np

from .barricade import Barricade
from .field import Field
from .line_of_sight import is_blocked, path_is_clear, sample_area, visible_ratio


@dataclass(frozen=True)
class Evaluation:
    score: int
    details: dict[str, float]


def clamp_score(value: float) -> float:
    return float(max(0.0, min(100.0, value)))


def evaluate_map(field: Field, barricades: list[Barricade]) -> Evaluation:
    bottom = field.bottom_start
    top = field.top_start
    center_points = sample_area(
        [field.width * 0.35, field.width * 0.5, field.width * 0.65],
        [field.height * 0.42, field.height * 0.5, field.height * 0.58],
    )
    left_points = sample_area([field.width * 0.22, field.width * 0.32], [field.height * 0.35, field.height * 0.5, field.height * 0.65])
    right_points = sample_area([field.width * 0.68, field.width * 0.78], [field.height * 0.35, field.height * 0.5, field.height * 0.65])

    start_to_start_blocked = is_blocked(bottom, top, barricades)
    bottom_center_open = visible_ratio([bottom], center_points, barricades)
    top_center_open = visible_ratio([top], center_points, barricades)
    cross_open = visible_ratio(left_points, right_points, barricades)

    start_safety = 100.0 if start_to_start_blocked else 25.0
    central_access = clamp_score(100.0 - abs(0.45 - bottom_center_open) * 95.0 - abs(0.45 - top_center_open) * 95.0)
    los_control = clamp_score(100.0 - cross_open * 80.0 - ((bottom_center_open + top_center_open) / 2.0) * 30.0)
    side_balance = clamp_score(100.0 - abs(left_cover_count(field, barricades) - right_cover_count(field, barricades)) * 12.0)
    density = density_score(field, barricades)
    route = route_score(field, barricades)
    central_strength = central_strength_score(field, barricades)

    weighted = (
        start_safety * 0.18
        + central_access * 0.18
        + side_balance * 0.16
        + los_control * 0.18
        + density * 0.12
        + route * 0.12
        + central_strength * 0.06
    )
    details = {
        "start_safety": round(start_safety, 1),
        "central_access": round(central_access, 1),
        "side_balance": round(side_balance, 1),
        "line_of_sight": round(los_control, 1),
        "density": round(density, 1),
        "route": round(route, 1),
        "central_strength": round(central_strength, 1),
    }
    return Evaluation(score=int(round(clamp_score(weighted))), details=details)


def left_cover_count(field: Field, barricades: list[Barricade]) -> int:
    return sum(1 for b in barricades if b.x < field.width / 2.0)


def right_cover_count(field: Field, barricades: list[Barricade]) -> int:
    return sum(1 for b in barricades if b.x >= field.width / 2.0)


def density_score(field: Field, barricades: list[Barricade]) -> float:
    target = field.width * field.height * 0.055
    cover_area = sum(b.polygon.area for b in barricades)
    return clamp_score(100.0 - abs(target - cover_area) / target * 100.0)


def central_strength_score(field: Field, barricades: list[Barricade]) -> float:
    center = np.array([field.width / 2.0, field.height / 2.0])
    near_center = 0
    for b in barricades:
        dist = hypot(b.x - center[0], b.y - center[1])
        if dist < min(field.width, field.height) * 0.23:
            near_center += 1
    return clamp_score(100.0 - max(0, near_center - 2) * 22.0)


def route_score(field: Field, barricades: list[Barricade]) -> float:
    lanes = [
        ((field.width * 0.18, 0.9), (field.width * 0.18, field.height - 0.9)),
        ((field.width * 0.5, 0.9), (field.width * 0.5, field.height - 0.9)),
        ((field.width * 0.82, 0.9), (field.width * 0.82, field.height - 0.9)),
    ]
    clear_lanes = sum(1 for start, end in lanes if path_is_clear(start, end, barricades))
    return [20.0, 58.0, 82.0, 100.0][clear_lanes]
