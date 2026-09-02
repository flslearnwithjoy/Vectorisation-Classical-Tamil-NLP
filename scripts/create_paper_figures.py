"""Create the two final paper figures from audited v3 aggregate results.

No corpus text or individual example is read or written by this script.
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


OUT = Path(__file__).parent / "figures" / "notebook_outputs"
OUT.mkdir(parents=True, exist_ok=True)


def register_lengths() -> None:
    sources = ["Naaladiyar", "Ezhuth.", "Soll.", "Porul.", "Thirukadukam"]
    pairs = np.array([393, 379, 287, 103, 100])
    verse_tokens = np.array([6328, 2692, 2915, 824, 1817])
    urai_tokens = np.array([10667, 21835, 15047, 7137, 5838])
    verse_mean = verse_tokens / pairs
    urai_mean = urai_tokens / pairs
    x = np.arange(len(sources))
    width = 0.36

    fig, ax = plt.subplots(figsize=(9.3, 4.8))
    ax.bar(x - width / 2, verse_mean, width, label="Verse", color="#4C78A8")
    ax.bar(x + width / 2, urai_mean, width, label="Urai", color="#F58518")
    ax.set_ylabel("Mean v3 word tokens per pair")
    ax.set_xticks(x, sources)
    ax.set_ylim(0, 78)
    ax.grid(axis="y", alpha=0.25)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, ncols=2, loc="upper left")
    for i, (v, u) in enumerate(zip(verse_mean, urai_mean)):
        ax.text(i, max(v, u) + 2.0, f"{u / v:.1f}$\\times$", ha="center", va="bottom", fontsize=10)
    fig.tight_layout()
    fig.savefig(OUT / "register_length_by_source.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def grammar_probe() -> None:
    labels = ["Linguistic\nregularities\n(n=13)", "Random line\nreorderings\n(n=99)", "Pooled word\norder\n(n=112)"]
    correct = np.array([100.0, 94.9, 95.5])
    x = np.arange(len(labels))

    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    bars = ax.bar(x, correct, width=0.58, color="#54A24B")
    ax.axhline(50, color="#555555", linewidth=1.2, linestyle="--", label="Chance (50%)")
    ax.set_ylabel("Original order preferred (%)")
    ax.set_xticks(x, labels)
    ax.set_ylim(0, 108)
    ax.grid(axis="y", alpha=0.25)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, loc="lower right")
    for bar, value in zip(bars, correct):
        ax.text(bar.get_x() + bar.get_width() / 2, value + 2.2, f"{value:.1f}%", ha="center", va="bottom")
    fig.tight_layout()
    fig.savefig(OUT / "grammar_probe_final.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    register_lengths()
    grammar_probe()
