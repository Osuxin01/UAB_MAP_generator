from dataclasses import dataclass
from pathlib import Path
import random

from .barricade import Barricade, create_barricade, random_angle
from .evaluator import Evaluation, evaluate_map
from .field import Field


@dataclass(frozen=True)
class GeneratedMap:
    name: str
    field: Field
    barricades: list[Barricade]
    evaluation: Evaluation
    attempt: int


DEFAULT_CONFIG = {
    "field_width": 8,
    "field_height": 18,
    "grid_size": 0.5,
    "triangle_count": 4,
    "trapezoid_count": 2,
    "diamond_count": 2,
    "large_triangle_count": 2,
    "min_score": 70,
    "max_attempts": 500,
    "output_format": "png",
    "output_dir": "./output",
    "seed": None,
}

MIN_BARRIER_GAP = 1.0


def generate_map(config: dict, index: int = 1) -> GeneratedMap:
    cfg = DEFAULT_CONFIG | config
    rng = random.Random(cfg.get("seed"))
    field = Field(float(cfg["field_width"]), float(cfg["field_height"]), float(cfg["grid_size"]))
    shape_counts = shape_counts_from_config(cfg)
    expected_count = sum(shape_counts.values())
    best: GeneratedMap | None = None

    for attempt in range(1, int(cfg["max_attempts"]) + 1):
        barricades = place_barricades(field, rng, shape_counts)
        evaluation = evaluate_map(field, barricades)
        generated = GeneratedMap(
            name=f"UAB Auto Map {index:02d}",
            field=field,
            barricades=barricades,
            evaluation=evaluation,
            attempt=attempt,
        )
        if best is None or better_candidate(generated, best, expected_count):
            best = generated
        if is_acceptable(field, barricades, evaluation, int(cfg["min_score"]), expected_count):
            return generated

    if best is None:
        raise RuntimeError("Failed to create any candidate map.")
    if len(best.barricades) != expected_count:
        raise RuntimeError(f"Failed to place all configured barricades after {cfg['max_attempts']} attempts.")
    return best


def shape_counts_from_config(config: dict) -> dict[str, int]:
    counts = {
        "triangle": int(config["triangle_count"]),
        "trapezoid": int(config["trapezoid_count"]),
        "diamond": int(config["diamond_count"]),
        "large_triangle": int(config["large_triangle_count"]),
    }
    for shape, count in counts.items():
        if count < 0:
            raise ValueError(f"{shape}_count must be 0 or greater.")
        if count % 2 != 0:
            raise ValueError(f"{shape}_count must be even to keep point symmetry.")
    if sum(counts.values()) <= 0:
        raise ValueError("At least one barricade must be configured.")
    return counts


def is_acceptable(field: Field, barricades: list[Barricade], evaluation: Evaluation, min_score: int, expected_count: int) -> bool:
    return (
        len(barricades) == expected_count
        and evaluation.score >= min_score
    )


def better_candidate(candidate: GeneratedMap, current: GeneratedMap, expected_count: int) -> bool:
    candidate_has_all = len(candidate.barricades) == expected_count
    current_has_all = len(current.barricades) == expected_count
    if candidate_has_all != current_has_all:
        return candidate_has_all
    return candidate.evaluation.score > current.evaluation.score


def place_barricades(field: Field, rng: random.Random, shape_counts: dict[str, int]) -> list[Barricade]:
    pending_shapes = shape_pair_plan(shape_counts)
    rng.shuffle(pending_shapes)
    target_count = len(pending_shapes) * 2
    barricades: list[Barricade] = []
    placement_attempts = target_count * 220

    anchors = tactical_anchor_points(field, len(pending_shapes), rng)
    for anchor in anchors:
        if not pending_shapes:
            return barricades
        shape = pending_shapes[0]
        angle = random_angle(rng, shape)
        candidate = create_snapped_barricade(field, shape, anchor[0], anchor[1], angle, rng)
        pair = [candidate, mirror_barricade(field, candidate)]
        if is_valid_pair(field, pair, barricades):
            barricades.extend(pair)
            pending_shapes.pop(0)

    for _ in range(placement_attempts):
        if not pending_shapes:
            break
        shape = pending_shapes[0]
        x = rng.uniform(0.75, field.width - 0.75)
        y = rng.uniform(1.5, field.height / 2.0 - 0.45)
        angle = random_angle(rng, shape)
        candidate = create_snapped_barricade(field, shape, x, y, angle, rng)
        pair = [candidate, mirror_barricade(field, candidate)]
        if is_valid_pair(field, pair, barricades):
            barricades.extend(pair)
            pending_shapes.pop(0)
    return barricades


def shape_pair_plan(shape_counts: dict[str, int]) -> list[str]:
    pairs: list[str] = []
    for shape, count in shape_counts.items():
        pairs.extend([shape] * (count // 2))
    return pairs


def create_snapped_barricade(
    field: Field,
    shape: str,
    x: float,
    y: float,
    angle: float,
    rng: random.Random,
) -> Barricade:
    candidate = create_barricade(shape, x, y, angle)
    vertices = list(candidate.polygon.exterior.coords)[:-1]
    vertex = rng.choice(vertices)
    grid_x, grid_y = nearest_grid_point(field, vertex[0], vertex[1])
    return create_barricade(shape, x + grid_x - vertex[0], y + grid_y - vertex[1], angle)


def nearest_grid_point(field: Field, x: float, y: float) -> tuple[float, float]:
    grid = field.grid_size
    snapped_x = round(x / grid) * grid
    snapped_y = round(y / grid) * grid
    return (
        min(field.width, max(0.0, snapped_x)),
        min(field.height, max(0.0, snapped_y)),
    )


def tactical_anchor_points(field: Field, count: int, rng: random.Random) -> list[tuple[float, float]]:
    y_levels = [field.height * 0.18, field.height * 0.28, field.height * 0.38, field.height * 0.46]
    x_pairs = [(field.width * 0.28, field.width * 0.72), (field.width * 0.38, field.width * 0.62)]
    points: list[tuple[float, float]] = [
        (field.width * 0.5 + rng.uniform(-0.2, 0.2), field.height * 0.42 + rng.uniform(-0.45, 0.15))
    ]
    for y in y_levels:
        pair = rng.choice(x_pairs)
        jitter_y = rng.uniform(-0.45, 0.45)
        points.append((pair[0] + rng.uniform(-0.35, 0.25), y + jitter_y))
        points.append((pair[1] + rng.uniform(-0.25, 0.35), y + rng.uniform(-0.45, 0.45)))
    rng.shuffle(points)
    return points[: max(count, len(points))]


def mirror_barricade(field: Field, barricade: Barricade) -> Barricade:
    return create_barricade(
        barricade.shape,
        field.width - barricade.x,
        field.height - barricade.y,
        (barricade.angle + 180.0) % 360.0,
    )


def is_valid_pair(field: Field, pair: list[Barricade], existing: list[Barricade]) -> bool:
    if len(pair) != 2:
        return False
    first, second = pair
    if first.polygon.distance(second.polygon) < MIN_BARRIER_GAP:
        return False
    if not is_valid_placement(field, first, existing):
        return False
    return is_valid_placement(field, second, existing + [first])


def is_valid_placement(field: Field, candidate: Barricade, existing: list[Barricade]) -> bool:
    if not field.contains_polygon(candidate.polygon):
        return False
    for zone in field.start_zones:
        if candidate.polygon.intersects(zone):
            return False
    if candidate.y < 1.1 or candidate.y > field.height - 1.1:
        return False
    if any(candidate.polygon.distance(item.polygon) < MIN_BARRIER_GAP for item in existing):
        return False
    central_band = field.height * 0.38 <= candidate.y <= field.height * 0.62
    if central_band:
        central_count = sum(1 for item in existing if field.height * 0.38 <= item.y <= field.height * 0.62)
        if central_count >= 3:
            return False
    return True


def output_path(config: dict, index: int) -> Path:
    cfg = DEFAULT_CONFIG | config
    extension = str(cfg["output_format"]).lower().lstrip(".")
    stem = "generated_map" if index == 1 else f"generated_map_{index:02d}"
    return Path(str(cfg["output_dir"])) / f"{stem}.{extension}"
