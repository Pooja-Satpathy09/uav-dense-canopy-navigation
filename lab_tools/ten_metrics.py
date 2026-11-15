"""Ten-metric statistics for one or more `experiment` result folders.

For every result folder (one checkpoint under one plan) this prints each benchmark
metric with its 95% confidence interval, and for every requested pair of folders a
paired test on the same flights (same scene and speed):

  binary metrics (goal_success, collision)  exact McNemar test
  continuous metrics                        Wilcoxon signed-rank test
  multiple comparisons                      Holm correction over the 8 flight metrics

Confidence intervals: Wilson for rates, scene-cluster bootstrap (2000 resamples) for means.
The two scene metrics (traversability, relative_gap_size) describe the scenes, not the
policy, so they are reported once per difficulty.

Usage:
  python ten_metrics.py RESULTS_DIR NAME [NAME ...] [--pair A B ...] [--out PREFIX]
Example:
  python lab_tools/ten_metrics.py benchmark_results fix_20k_height height_20k_height \
      --pair fix_20k_height height_20k_height --out benchmark_results/ten_metrics_height
"""
import argparse
import csv
import json
import math
import random
import statistics
from collections import defaultdict
from pathlib import Path

FLIGHT = [("goal_success", "rate", "higher"), ("collision", "rate", "lower"),
          ("min_obstacle_clearance_m", "m", "higher"), ("path_excess_factor", "1", "lower"),
          ("average_speed_mps", "m/s", ""), ("relative_end_distance", "1", "lower"),
          ("speed_rmse_mps", "m/s", "lower"), ("jerk_rms_mps3", "m/s^3", "lower")]
SCENE = [("traversability", "1"), ("relative_gap_size", "1")]
BINARY = {"goal_success", "collision"}


def wilson(k, n, z=1.959963984540054):
    if n == 0:
        return float("nan"), float("nan")
    p, den = k / n, 1 + z * z / n
    c, h = (p + z * z / (2 * n)) / den, z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return max(0.0, c - h), min(1.0, c + h)


def bootstrap_mean_ci(pairs, resamples=2000):
    """pairs: [(scene_id, value)]; resample whole scenes (both speeds stay together)."""
    clusters = defaultdict(list)
    for sid, v in pairs:
        clusters[sid].append(v)
    ids, rng, means = sorted(clusters), random.Random(2026), []
    if len(ids) < 2:
        return float("nan"), float("nan")
    for _ in range(resamples):
        picked = [v for _ in ids for v in clusters[rng.choice(ids)]]
        means.append(statistics.fmean(picked))
    means.sort()
    return means[int(0.025 * (resamples - 1))], means[int(0.975 * (resamples - 1))]


def mcnemar_exact(b, c):
    n = b + c
    if n == 0:
        return 1.0
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(min(b, c) + 1)) / 2 ** n)


def wilcoxon_p(diffs):
    diffs = [d for d in diffs if d != 0]
    if not diffs:
        return 1.0
    try:
        from scipy.stats import wilcoxon
        return float(wilcoxon(diffs).pvalue)
    except Exception:                                    # normal approximation fallback
        n = len(diffs)
        order = sorted(range(n), key=lambda i: abs(diffs[i]))
        ranks, i = [0.0] * n, 0
        while i < n:
            j = i
            while j + 1 < n and abs(diffs[order[j + 1]]) == abs(diffs[order[i]]):
                j += 1
            for k in range(i, j + 1):
                ranks[order[k]] = (i + j) / 2 + 1
            i = j + 1
        w = sum(r for r, d in zip(ranks, diffs) if d > 0)
        mu, sd = n * (n + 1) / 4, math.sqrt(n * (n + 1) * (2 * n + 1) / 24)
        z = (abs(w - mu) - 0.5) / sd if sd else 0.0
        return math.erfc(z / math.sqrt(2))


def holm(pvalues):
    m, order = len(pvalues), sorted(range(len(pvalues)), key=lambda i: pvalues[i])
    adjusted, running = [1.0] * m, 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (m - rank) * pvalues[i]))
        adjusted[i] = running
    return adjusted


def load(results_dir, name):
    flights = {}
    for path in sorted((Path(results_dir) / name).glob("run_[0-9][0-9][0-9][0-9][0-9]/result.metrics.json")):
        r = json.loads(path.read_text())
        key = (r["scene_id"], float(r["config"]["target_speed_mps"]))
        flights[key] = {"difficulty": r["difficulty"], "termination": r["termination"],
                        **{m: r["metrics"].get(m, {}).get("value") for m, *_ in FLIGHT + SCENE}}
    if not flights:
        raise SystemExit(f"No result.metrics.json found under {Path(results_dir) / name}")
    return flights


def fmt(x, digits=3):
    return "n/a" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.{digits}f}"


def per_run_rows(name, flights):
    rows = []
    for metric, unit, better in FLIGHT:
        pairs = [(k[0], float(f[metric])) for k, f in flights.items() if f[metric] is not None]
        n = len(pairs)
        if metric in BINARY:
            k = sum(v for _, v in pairs)
            lo, hi = wilson(int(k), n)
            rows.append({"run": name, "metric": metric, "unit": unit, "better": better, "n": n,
                         "estimate": k / n if n else float("nan"), "sd": "", "median": "",
                         "ci_low": lo, "ci_high": hi, "ci_method": "Wilson"})
        else:
            vals = [v for _, v in pairs]
            lo, hi = bootstrap_mean_ci(pairs)
            rows.append({"run": name, "metric": metric, "unit": unit, "better": better, "n": n,
                         "estimate": statistics.fmean(vals) if vals else float("nan"),
                         "sd": statistics.stdev(vals) if n > 1 else float("nan"),
                         "median": statistics.median(vals) if vals else float("nan"),
                         "ci_low": lo, "ci_high": hi, "ci_method": "scene bootstrap"})
    return rows


def pair_rows(a_name, a, b_name, b):
    keys = sorted(set(a) & set(b))
    rows = []
    for metric, unit, better in FLIGHT:
        both = [(a[k][metric], b[k][metric]) for k in keys
                if a[k][metric] is not None and b[k][metric] is not None]
        n = len(both)
        if metric in BINARY:
            only_a = sum(1 for x, y in both if x and not y)
            only_b = sum(1 for x, y in both if y and not x)
            p, test = mcnemar_exact(only_a, only_b), f"McNemar (A only {only_a}, B only {only_b})"
        else:
            p, test = wilcoxon_p([float(y) - float(x) for x, y in both]), "Wilcoxon signed-rank"
        rows.append({"A": a_name, "B": b_name, "metric": metric, "unit": unit, "better": better,
                     "n_pairs": n, "mean_A": statistics.fmean(float(x) for x, _ in both) if n else float("nan"),
                     "mean_B": statistics.fmean(float(y) for _, y in both) if n else float("nan"),
                     "test": test, "p": p})
    for row, adj in zip(rows, holm([r["p"] for r in rows])):
        row["p_holm"] = adj
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("results_dir")
    ap.add_argument("names", nargs="+")
    ap.add_argument("--pair", nargs=2, action="append", default=[], metavar=("A", "B"))
    ap.add_argument("--out", help="write PREFIX.md, PREFIX_per_run.csv and PREFIX_paired.csv")
    args = ap.parse_args()
    data = {n: load(args.results_dir, n) for n in dict.fromkeys(args.names + [x for p in args.pair for x in p])}

    lines = ["## Ten-metric statistics", "",
             "Rates: Wilson 95% CI. Means: 95% CI from a scene-cluster bootstrap (2000 resamples).", ""]
    per_run = []
    for name, flights in data.items():
        rows = per_run_rows(name, flights)
        per_run += rows
        lines += [f"### {name} ({len(flights)} flights)", "",
                  "| Metric | Unit | Better | Estimate | 95% CI | SD | Median |", "|---|---|---|---|---|---|---|"]
        for r in rows:
            lines.append(f"| {r['metric']} | {r['unit']} | {r['better'] or '-'} | {fmt(r['estimate'])} | "
                         f"[{fmt(r['ci_low'])}, {fmt(r['ci_high'])}] | {fmt(r['sd']) if r['sd'] != '' else '-'} | "
                         f"{fmt(r['median']) if r['median'] != '' else '-'} |")
        lines.append("")

    first = next(iter(data.values()))
    scenes = {}
    for (sid, _), f in first.items():
        scenes[sid] = f
    lines += ["### Scene metrics (properties of the test scenes, same for every checkpoint)", "",
              "| Difficulty | Scenes | traversability (mean) | relative_gap_size (mean) |", "|---|---|---|---|"]
    by_diff = defaultdict(list)
    for f in scenes.values():
        by_diff[f["difficulty"]].append(f)
    for diff in sorted(by_diff):
        g = by_diff[diff]
        cells = []
        for m, _ in SCENE:
            vals = [float(x[m]) for x in g if x[m] is not None]
            cells.append(fmt(statistics.fmean(vals)) if vals else "n/a")
        lines.append(f"| {diff} | {len(g)} | {cells[0]} | {cells[1]} |")
    lines.append("")

    paired = []
    for a_name, b_name in args.pair:
        rows = pair_rows(a_name, data[a_name], b_name, data[b_name])
        paired += rows
        lines += [f"### Paired: A = {a_name} vs B = {b_name} (same scene and speed)", "",
                  "| Metric | Better | Mean A | Mean B | n | Test | p | p (Holm) |", "|---|---|---|---|---|---|---|---|"]
        for r in rows:
            star = " *" if r["p_holm"] < 0.05 else ""
            lines.append(f"| {r['metric']} | {r['better'] or '-'} | {fmt(r['mean_A'])} | {fmt(r['mean_B'])} | "
                         f"{r['n_pairs']} | {r['test']} | {fmt(r['p'], 4)} | {fmt(r['p_holm'], 4)}{star} |")
        lines += ["", "* = significant at 0.05 after Holm correction over the 8 flight metrics.", ""]

    text = "\n".join(lines)
    print(text)
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.with_suffix(".md").write_text(text + "\n")
        for suffix, rows in (("_per_run.csv", per_run), ("_paired.csv", paired)):
            if rows:
                with open(f"{out}{suffix}", "w", newline="") as fh:
                    w = csv.DictWriter(fh, fieldnames=list(rows[0]))
                    w.writeheader()
                    w.writerows(rows)
        print(f"\nWrote {out.with_suffix('.md')} and CSV files next to it.")


if __name__ == "__main__":
    main()
