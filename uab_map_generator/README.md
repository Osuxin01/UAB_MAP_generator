# UAB Map Generator

Python 3 command line tool for automatically generating 2D UAB map candidates.

## Features

- Field, 1 m grid, start points, and barricades are rendered to PNG or SVG.
- Triangle, diamond, trapezoid, and large triangle barricades are placed randomly.
- Candidate maps are rejected when barricades overlap, leave the field, or touch start zones.
- A simple line-of-sight and balance evaluator scores each candidate out of 100.
- `config.json` controls field size, shape counts, score threshold, output format, and output directory.

## Setup

```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

Use a custom config:

```bash
python main.py --config config.json
```

Generate multiple maps:

```bash
python main.py --count 10
```

Shape counts are configured in `config.json`:

```json
{
  "triangle_count": 4,
  "trapezoid_count": 2,
  "diamond_count": 2,
  "large_triangle_count": 2
}
```

Because maps are generated with point symmetry, each shape count must be an even number.

Generated images are written to `output/` by default.

## Notes

This initial version is intended to produce useful map drafts for human review and adjustment. The evaluator is deliberately simple and should be tuned with real play feedback.
