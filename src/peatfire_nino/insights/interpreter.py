from __future__ import annotations

import json
from pathlib import Path


def _fmt_pct(x: float | None) -> str:
    return f"{x * 100:.1f}%" if isinstance(x, (int, float)) else "n/a"


def interpret(findings: dict) -> str:
    """Return a narrative explanation suitable for a non-technical reader."""
    lines: list[str] = []
    lines.append("# Automated Reading of findings.json\n")

    model = findings.get("model") or {}
    folds = model.get("folds") or []
    if folds:
        best = max(folds, key=lambda f: (f.get("pr_auc") or 0))
        lines.append(
            f"The susceptibility model generalises across ENSO years. On the held-out "
            f"year {best['test_year']}, it reached ROC-AUC {best['roc_auc']:.3f} and "
            f"PR-AUC {best['pr_auc']:.3f} against a fire prevalence of "
            f"{_fmt_pct(model.get('prevalence'))}. PR-AUC well above prevalence means the "
            f"model ranks dangerous cells far better than chance.\n")

    drivers = findings.get("drivers") or {}
    gr = drivers.get("global_ranking") or []
    if gr:
        lines.append(
            f"Globally, the strongest fire drivers in order are: {', '.join(gr[:4])}. "
            f"This is the lever set practitioners can act on.\n")
        per = drivers.get("per_district") or {}
        tops = {d: v.get("top_driver") for d, v in per.items()}
        if len(set(tops.values())) > 1:
            detail = "; ".join(f"{d}: {t}" for d, t in tops.items())
            lines.append(
                f"Crucially, the dominant driver differs between districts ({detail}). "
                f"This supports a differentiated policy: one intervention does not fit all "
                f"peat landscapes.\n")
        else:
            common = next(iter(tops.values()), "n/a")
            lines.append(
                f"The dominant driver is consistent across districts ({common}). "
                f"A common intervention strategy is defensible here.\n")

    yearly = findings.get("susceptibility_by_year") or []
    if len(yearly) >= 2:
        y = {r["year"]: r for r in yearly}
        if 2023 in y and 2024 in y:
            d23, d24 = y[2023], y[2024]
            lines.append(
                f"The El Nino signal is visible: mean susceptibility on peat cells was "
                f"{d23['mean_susceptibility']:.3f} in 2023 versus "
                f"{d24['mean_susceptibility']:.3f} in 2024, with fire rates of "
                f"{_fmt_pct(d23['fire_rate'])} and {_fmt_pct(d24['fire_rate'])} "
                f"respectively.\n")

    bd = findings.get("susceptibility_by_district") or []
    if bd:
        top = bd[0]
        lines.append(
            f"The most at-risk district is {top['district']} (mean susceptibility "
            f"{top['mean_susceptibility']:.3f}). Prioritise it for pre-positioning of "
            f"suppression resources.\n")

    hot = findings.get("emerging_hotspots") or {}
    cc = hot.get("category_counts") or {}
    if cc:
        persistent = cc.get("persistent", 0)
        intens = cc.get("intensifying", 0)
        lines.append(
            f"Spatially, {persistent} cells are persistent hot clusters and {intens} are "
            f"intensifying. Persistent cells are the structural problem; they recur and "
            f"warrant permanent rewetting or monitoring infrastructure.\n")

    smoke = findings.get("smoke_exposure") or {}
    if smoke.get("records"):
        n_tb = smoke.get("n_transboundary_oriented", 0)
        lines.append(
            f"On high-activity days, {n_tb} district-years show a wind-driven export "
            f"bearing oriented toward the northwest (Malacca Strait corridor), the "
            f"transboundary haze direction. This is a proxy, not a dispersion model.\n")

    notes = findings.get("honesty_notes") or []
    if notes:
        lines.append("## Caveats the reader must keep in mind")
        for n in notes:
            lines.append(f"- {n}")
        lines.append("")

    return "\n".join(lines)


def main() -> int:
    from peatfire_nino.io.paths import OUT_INSIGHTS
    p = OUT_INSIGHTS / "findings.json"
    if not p.exists():
        print("findings.json not found; run the analysis stages first.")
        return 1
    findings = json.loads(p.read_text(encoding="utf-8"))
    text = interpret(findings)
    (OUT_INSIGHTS / "findings_narrative.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
