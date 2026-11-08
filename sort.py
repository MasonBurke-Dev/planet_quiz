"""Point-based scoring using percentile groups, dynamic group weights and neighbor points.

How one question works (for example "temperature"):
    1. Planets are split into percentile groups (default 5: 0 = lowest 20% ...
       4 = highest 20%) for that category.
    2. The user picks the group(s) they want, such as group 4 for "hottest".
    3. A planet earns points for how close its group is to a picked group:
         - picked group: full points
         - 1 step away:  `falloff` of the points (default 50%)
         - 2 steps away: falloff squared (25%), and so on up to `reach` steps
         - further away: 0
    4. DYNAMIC WEIGHT: points are also scaled by where the planet's own group sits.
       Edge groups count fully, the middle group counts `middle_weight` of the
       full amount (default 0.5), with a smooth ramp in between.
    5. Points = question weight x closeness x group multiplier.

Overall score = points earned / best points possible for the categories the
planet has data for, scaled to 0-100.

Example:
    from sort import GroupPreference, score_by_groups

    prefs = [
        GroupPreference("temperature", selected=(2, 3), weight=9),
        GroupPreference("gravity",     selected=(2,),    weight=6),
        GroupPreference("distance",    selected=(0,),    weight=3),  # closest 20%
    ]
    ranked = score_by_groups(table, prefs, min_coverage=0.7)
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from utils import percentile_labels


@dataclass
class GroupPreference:
    """Everything one slider-based question controls."""

    column: str                      # table column this question is about
    selected: tuple = (4,)           # preferred group numbers (0 = lowest percentile group)
    weight: float = 5.0              # importance slider (0 = ignore, 10 = very important)
    n_groups: int = 5                # how many percentile groups to split into
    falloff: float = 0.5             # share of points kept per step away from a picked group
    reach: int = 2                   # how many steps away still earn points
    middle_weight: float = 0.5       # multiplier for the middle group (1.0 = all groups equal)
    label: str | None = None         # friendly name for the UI


def select_range(low_pct, high_pct, n_groups=5):
    """Turn a percentile range slider (like 60 to 100) into group numbers.
    Every group that overlaps the range is selected."""
    return tuple(
        g for g in range(n_groups)
        if (g + 1) / n_groups * 100 > low_pct and g / n_groups * 100 < high_pct
    )


def points_by_group(pref):
    """Return the share of the question's weight a planet earns from each group
    (a list with one value per group). Useful for previewing a question in the UI."""
    n = pref.n_groups
    picked = sorted(set(pref.selected))
    if not picked:
        raise ValueError(f"'{pref.column}': pick at least one group.")
    if picked[0] < 0 or picked[-1] >= n:
        raise ValueError(f"'{pref.column}': groups must be between 0 and {n - 1}.")

    center = (n - 1) / 2
    shares = []
    for g in range(n):
        steps = min(abs(g - s) for s in picked)
        closeness = 0.0 if steps > pref.reach else pref.falloff ** steps

        # Dynamic weight: 1.0 at the edges, middle_weight in the middle
        edge = abs(g - center) / center if center > 0 else 1.0
        multiplier = pref.middle_weight + (1 - pref.middle_weight) * edge

        shares.append(closeness * multiplier)
    return np.array(shares)


def score_by_groups(df, preferences, name_col="planet", min_coverage=0.0):
    """Score every planet and return them best-first.

    Returns a table (same index as `df`) with:
        name_col         planet name
        score            0-100 match, relative to the best possible for that planet's data
        coverage         0-1, share of the total best-possible points the planet has data for
        pts_<column>     points earned in each category

    Notes:
      - Groups are ranked within the `df` you pass in, so filter by planet type
        first if you want like-for-like groups.
      - Planets missing a value are not punished; their score is averaged over
        the categories they do have. Use `min_coverage` to hide sparse ones.
      - Questions with weight 0, or whose column is missing or has too few
        values, are skipped.
    """
    result = pd.DataFrame({name_col: df[name_col]})
    points_total = pd.Series(0.0, index=df.index)
    best_with_data = pd.Series(0.0, index=df.index)
    best_overall = 0.0

    for p in preferences:
        if p.weight <= 0 or p.column not in df.columns:
            continue
        try:
            labels = percentile_labels(df[p.column], p.n_groups)
        except ValueError:
            continue

        shares = points_by_group(p)
        best = shares.max() * p.weight
        if best <= 0:
            continue

        has_data = labels.notna()
        idx = labels.fillna(0).astype(int).to_numpy()
        points = pd.Series(np.where(has_data, shares[idx] * p.weight, np.nan), index=df.index)

        result[f"pts_{p.column}"] = points
        points_total += points.fillna(0.0)
        best_with_data += has_data * best
        best_overall += best

    if best_overall == 0:
        raise ValueError("No usable questions: check weights, groups and column names.")

    result["coverage"] = best_with_data / best_overall
    result["score"] = 100 * points_total / best_with_data.replace(0, np.nan)

    result = result[result["coverage"] >= min_coverage]
    ordered = [name_col, "score", "coverage"] + [c for c in result.columns if c.startswith("pts_")]
    return result[ordered].sort_values("score", ascending=False)


def default_group_preferences():
    """A starting set of preferences for the question columns used by main.py."""
    return [
        GroupPreference("temperature", selected=(2,), weight=8, label="Temperature"),
        GroupPreference("size", selected=(2,), weight=6, label="Size"),
        GroupPreference("mass", selected=(2,), weight=6, label="Mass"),
        GroupPreference("gravity", selected=(2,), weight=6, label="Gravity"),
        GroupPreference("brightness", selected=(2,), weight=6, label="Brightness"),
        GroupPreference("distance", selected=(0,), weight=6, label="Distance"),
        GroupPreference("star_age", selected=(2,), weight=6, label="Star age"),
        GroupPreference("metallicity", selected=(2,), weight=6, label="Metallicity"),
        GroupPreference("neighbors", selected=(2,), weight=6, label="Neighbors"),
        GroupPreference("solidity", selected=(4,), weight=6, label="Solidity"),
    ]


if __name__ == "__main__":
    demo = pd.DataFrame(
        {
            "planet": [f"P{i}" for i in range(10)],
            "temperature": [-80, -40, -10, 0, 5, 15, 22, 40, 90, np.nan],
            "distance": [300, 120, 80, 50, 40, 25, 12, 8, 5, 2],
        }
    )
    pref = GroupPreference("temperature", selected=(4,), weight=5)
    print("points per group:", points_by_group(pref).round(3))
    print("slider 60-100% ->", select_range(60, 100))

    prefs = [
        GroupPreference("temperature", selected=(3, 4), weight=9),
        GroupPreference("distance", selected=(4,), weight=3),
    ]
    print(score_by_groups(demo, prefs).round(2))