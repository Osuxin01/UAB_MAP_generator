from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon as MplPolygon, Rectangle

from .barricade import seam_lines_for_barricade
from .generator import GeneratedMap


def render_map(generated: GeneratedMap, output_path: Path) -> None:
    field = generated.field
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig_width = max(5.0, field.width * 0.55)
    fig_height = max(8.0, field.height * 0.55)
    fig, ax = plt.subplots(figsize=(fig_width, fig_height), dpi=180)
    ax.set_facecolor("#f7f8fa")
    ax.add_patch(Rectangle((0, 0), field.width, field.height, fill=False, edgecolor="black", linewidth=2.0))

    draw_grid(ax, field)
    draw_starts(ax, generated)
    draw_barricades(ax, generated)

    ax.set_xlim(-0.35, field.width + 0.35)
    ax.set_ylim(-0.35, field.height + 0.8)
    ax.set_aspect("equal", adjustable="box")
    ax.set_title(f"{generated.name}  |  Score: {generated.evaluation.score}/100", fontsize=11, pad=12)
    detail = "  ".join(short_detail(key, value) for key, value in generated.evaluation.details.items())
    ax.text(field.width / 2.0, field.height + 0.35, detail, ha="center", va="center", fontsize=5.8, color="#333333")
    ax.set_xlabel("meters")
    ax.set_ylabel("meters")
    fig.tight_layout()
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)


def draw_grid(ax, field) -> None:
    minor = field.grid_size
    major = 1.0
    x = 0.0
    while x <= field.width + 1e-9:
        is_major = abs((x / major) - round(x / major)) < 1e-9
        ax.plot([x, x], [0, field.height], color="#c9ced6" if is_major else "#e4e7ec", linewidth=0.55 if is_major else 0.35, zorder=0)
        x += minor
    y = 0.0
    while y <= field.height + 1e-9:
        is_major = abs((y / major) - round(y / major)) < 1e-9
        ax.plot([0, field.width], [y, y], color="#c9ced6" if is_major else "#e4e7ec", linewidth=0.55 if is_major else 0.35, zorder=0)
        y += minor


def draw_starts(ax, generated: GeneratedMap) -> None:
    for label, point in [("START A", generated.field.bottom_start), ("START B", generated.field.top_start)]:
        ax.add_patch(Circle(point, 0.28, facecolor="#d93a35", edgecolor="#8f1d1b", linewidth=1.2, zorder=4))
        offset = 0.45 if point[1] < generated.field.height / 2.0 else -0.45
        ax.text(point[0], point[1] + offset, label, ha="center", va="center", fontsize=7, color="#8f1d1b", weight="bold")


def draw_barricades(ax, generated: GeneratedMap) -> None:
    for barricade in generated.barricades:
        coords = list(barricade.polygon.exterior.coords)
        patch = MplPolygon(coords, closed=True, facecolor="#2f73d8", edgecolor="#123d80", linewidth=1.2, alpha=0.9, zorder=3)
        ax.add_patch(patch)
        for seam in seam_lines_for_barricade(barricade):
            x_values, y_values = seam.xy
            ax.plot(x_values, y_values, color="#4cc9df", linewidth=0.8, alpha=0.85, zorder=4)


def short_detail(key: str, value: float) -> str:
    labels = {
        "start_safety": "Safety",
        "central_access": "Access",
        "side_balance": "Balance",
        "line_of_sight": "LOS",
        "density": "Density",
        "route": "Route",
        "central_strength": "Center",
    }
    return f"{labels.get(key, key)} {value:g}"
