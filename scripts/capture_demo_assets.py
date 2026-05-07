#!/usr/bin/env python3
"""Draw a static pipeline diagram for docs (no Spider required)."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "assets" / "demo"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8.5, 3.2))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 4)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    boxes = [
        (0.3, 2.2, 1.8, 1.1, "Spider\nschema"),
        (2.5, 2.2, 1.8, 1.1, "Chroma\nindex"),
        (4.7, 2.2, 1.8, 1.1, "Schema\nlinker"),
        (6.9, 2.2, 1.8, 1.1, "Few-shot\nretrieve"),
        (2.5, 0.5, 4.0, 1.1, "Generate → validate → SQLite exec"),
    ]
    for x, y, w, h, label in boxes:
        patch = FancyBboxPatch(
            (x, y), w, h, boxstyle="round,pad=0.05", linewidth=1.2, edgecolor="#333", facecolor="#eef2ff"
        )
        ax.add_patch(patch)
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", fontsize=9)

    arrows = [
        ((2.1, 2.75), (2.5, 2.75)),
        ((4.3, 2.75), (4.7, 2.75)),
        ((6.5, 2.75), (6.9, 2.75)),
        ((7.8, 2.2), (4.5, 1.6)),
        ((3.5, 2.2), (4.5, 1.6)),
    ]
    for (x0, y0), (x1, y1) in arrows:
        ax.annotate(
            "",
            xy=(x1, y1),
            xytext=(x0, y0),
            arrowprops=dict(arrowstyle="->", color="#444", lw=1.2),
        )

    ax.text(5, 3.7, "text2sql-rag — Phase 2/3 pipeline (concept)", ha="center", fontsize=11, weight="bold")
    fig.tight_layout()
    fig.savefig(OUT / "pipeline_overview.png", dpi=150)
    plt.close(fig)
    print(f"Wrote {OUT / 'pipeline_overview.png'}")


if __name__ == "__main__":
    main()
