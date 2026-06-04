import argparse
import json
import os
from pathlib import Path

from src.generator import DEFAULT_CONFIG, generate_map, output_path


def load_config(path: Path) -> dict:
    if not path.exists():
        return DEFAULT_CONFIG.copy()
    with path.open("r", encoding="utf-8") as file:
        user_config = json.load(file)
    return DEFAULT_CONFIG | user_config


def prepare_runtime(project_dir: Path) -> None:
    mpl_config = project_dir / ".matplotlib"
    mpl_config.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(mpl_config))


def resolve_output_dir(config: dict, config_path: Path, project_dir: Path) -> dict:
    output_dir = Path(str(config["output_dir"]))
    base_dir = config_path.parent if config_path.exists() else project_dir
    if not output_dir.is_absolute():
        output_dir = base_dir / output_dir
    return config | {"output_dir": str(output_dir)}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate UAB 2D competition maps.")
    parser.add_argument("--config", default="config.json", help="Path to config JSON.")
    parser.add_argument("--count", type=int, default=1, help="Number of maps to generate.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    project_dir = Path(__file__).resolve().parent
    prepare_runtime(project_dir)

    from src.renderer import render_map

    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = project_dir / config_path
    config = resolve_output_dir(load_config(config_path), config_path, project_dir)

    for index in range(1, args.count + 1):
        generated = generate_map(config, index=index)
        path = output_path(config, index)
        render_map(generated, path)
        print(
            f"generated {path} score={generated.evaluation.score} "
            f"attempt={generated.attempt} barricades={len(generated.barricades)}"
        )


if __name__ == "__main__":
    main()
