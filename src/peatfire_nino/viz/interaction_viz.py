"""interaction_viz.py
Visualise SHAP interactions and partial dependence curves.
"""
from __future__ import annotations

import json

import matplotlib.pyplot as plt

from peatfire_nino.io.logging_utils import log_step
from peatfire_nino.io.paths import OUT_FIGURES, OUT_TABLES

_DPI = 300


def render_interaction_figures() -> None:
    p = OUT_TABLES / "shap_interactions.json"
    if not p.exists():
        log_step("shap_interactions.json missing", "WARN")
        return
    d = json.loads(p.read_text(encoding="utf-8"))

    # --- PDP curves (one panel per driver) ---
    pdp = d["partial_dependence"]
    feats = list(pdp.keys())
    if feats:
        fig, axes = plt.subplots(1, len(feats), figsize=(4 * len(feats), 4))
        if len(feats) == 1:
            axes = [axes]
        for ax, f in zip(axes, feats):
            xs = [c["bin_center"] for c in pdp[f]]
            ys = [c["mean_fire_prob"] for c in pdp[f]]
            ax.plot(xs, ys, "o-", color="#b63a1c", lw=2)
            ax.set_xlabel(f)
            ax.set_ylabel("mean fire probability")
            ax.set_title(f"Partial dependence: {f}", fontsize=10)
            ax.grid(alpha=0.3)
        fig.suptitle("How fire probability responds to dryness",
                     fontweight="bold")
        fig.tight_layout()
        fig.savefig(OUT_FIGURES / "chart_partial_dependence.png", dpi=_DPI)
        plt.close(fig)

    # --- Interaction bar chart ---
    pairs = d["top_interactions"]
    if pairs:
        labels = [f"{p['feature_a']}\nx {p['feature_b']}" for p in pairs]
        vals = [p["interaction_strength"] for p in pairs]
        fig, ax = plt.subplots(figsize=(7, 4.5))
        ax.barh(labels[::-1], vals[::-1], color="#3f6f73")
        ax.set_xlabel("Mean |SHAP interaction|")
        ax.set_title("Strongest driver interactions (compound dryness)",
                     fontweight="bold", loc="left")
        fig.tight_layout()
        fig.savefig(OUT_FIGURES / "chart_interactions.png", dpi=_DPI)
        plt.close(fig)

    log_step("interaction figures rendered", "OK")


def main() -> int:
    render_interaction_figures()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
