"""Utilities for splitting planet data into percentile groups.

Example:
    from utils import split_into_percentiles

    groups = split_into_percentiles(table, "temperature")
    groups[0]   # coldest 20% of planets (planet names)
    groups[4]   # hottest 20% of planets
"""

import numpy as np
import pandas as pd


def split_into_percentiles(
    df,
    column,
    n_groups=5,
    name_col="planet",
    ascending=True,
    as_records=False,
):
    """Sort the data by `column` and split it into `n_groups` equal-sized groups.

    With the default n_groups=5 each group is a 20% slice (a quintile):
        groups[0] = lowest 0-20%, groups[1] = 20-40%, ... groups[4] = highest 80-100%

    Returns a list of `n_groups` lists. Each inner list holds the planet names
    from `name_col`, or full row dictionaries if as_records=True.

    - Rows where `column` is missing (NaN) are skipped, since they can't be ranked.
    - Groups are split by position, so sizes differ by at most 1 even when many
      planets share the same value.
    - ascending=False puts the highest values in groups[0] instead.
    """
    if n_groups < 1:
        raise ValueError("n_groups must be at least 1")

    data = df.dropna(subset=[column]).sort_values(column, ascending=ascending, kind="stable")
    if len(data) < n_groups:
        raise ValueError(
            f"Only {len(data)} planets have a value for '{column}', "
            f"which is not enough for {n_groups} groups."
        )

    # Split row positions into n_groups nearly equal chunks, in sorted order
    position_chunks = np.array_split(np.arange(len(data)), n_groups)

    groups = []
    for positions in position_chunks:
        chunk = data.iloc[positions]
        if as_records:
            groups.append(chunk.to_dict("records"))
        else:
            groups.append(chunk[name_col].tolist())
    return groups


def percentile_edges(df, column, n_groups=5):
    """Return the cutoff values between groups, e.g. for 5 groups the values at
    0%, 20%, 40%, 60%, 80% and 100%. Handy for labeling each group's range."""
    values = df[column].dropna()
    return np.percentile(values, np.linspace(0, 100, n_groups + 1)).tolist()


def split_by_type_then_percentile(
    df,
    type_col,
    column,
    n_groups=5,
    name_col="planet",
    ascending=True,
    as_records=False,
):
    """Split into percentile groups separately within each planet type, so one
    type (like gas giants) doesn't skew the groups of another.

    Returns a dictionary: {type_name: [list_1, list_2, ... list_n]}.
    Types with too few planets for `n_groups` are skipped.
    """
    results = {}
    for type_name, subset in df.groupby(type_col, observed=True):
        try:
            results[type_name] = split_into_percentiles(
                subset, column, n_groups, name_col, ascending, as_records
            )
        except ValueError:
            continue
    return results


def percentile_labels(values, n_groups=5):
    """Give every value a group number from 0 (lowest percentile group) to
    n_groups - 1 (highest). Missing values stay NaN. Returns a Series with the
    same index as `values`, so it can be added to a table as a column.

    This is the fast, one-column alternative to split_into_percentiles.
    """
    s = pd.Series(values, dtype=float)
    valid = s.notna()
    count = int(valid.sum())
    if count < n_groups:
        raise ValueError(f"Only {count} values available, not enough for {n_groups} groups.")
    labels = pd.Series(np.nan, index=s.index)
    ranks = s[valid].rank(method="first")            # 1..count, ties broken by order
    labels[valid] = ((ranks - 1) * n_groups // count)  # evenly spread 0..n_groups-1
    return labels


# Categories (columns) used when you don't pass your own list
DEFAULT_CATEGORIES = [
    "temperature",
    "size",
    "mass",
    "gravity",
    "brightness",
    "distance",
    "star_age",
    "metallicity",
    "neighbors",
    "solidity",
]


def split_all_categories(
    df,
    categories=None,
    n_groups=5,
    type_col=None,
    name_col="planet",
    ascending=True,
    as_records=False,
):
    """Run the percentile split for many categories at once, using the same
    function each time (no code is needed per category).

    categories: list of column names. Defaults to DEFAULT_CATEGORIES.
    type_col:   optional column (like "solid_label"). If given, each category is
                split separately within each planet type.

    Returns:
        without type_col: {category: [list_1, ... list_n]}
        with type_col:    {category: {type_name: [list_1, ... list_n]}}

    Categories that are missing from the table, or that have too few values
    for `n_groups`, are skipped.
    """
    if categories is None:
        categories = DEFAULT_CATEGORIES

    results = {}
    for category in categories:
        if category not in df.columns:
            continue
        try:
            if type_col is None:
                results[category] = split_into_percentiles(
                    df, category, n_groups, name_col, ascending, as_records
                )
            else:
                by_type = split_by_type_then_percentile(
                    df, type_col, category, n_groups, name_col, ascending, as_records
                )
                if by_type:
                    results[category] = by_type
        except ValueError:
            continue
    return results


if __name__ == "__main__":
    # Small demo with made-up data
    demo = pd.DataFrame(
        {
            "planet": [f"Planet {i}" for i in range(1, 13)],
            "temperature": [-80, -40, -10, 0, 5, 15, 22, 40, 90, 150, 300, None],
            "solid_label": ["Solid (rocky)"] * 8 + ["Gaseous / volatile-rich"] * 4,
        }
    )

    groups = split_into_percentiles(demo, "temperature")
    for i, g in enumerate(groups):
        print(f"Group {i + 1} ({i * 20}-{(i + 1) * 20}%): {g}")

    print("Edges:", percentile_edges(demo, "temperature"))
    print(split_by_type_then_percentile(demo, "solid_label", "temperature", n_groups=2))

    # Every category at once
    demo["gravity"] = [0.3, 0.5, 0.8, 1.0, 1.1, 1.4, 1.8, 2.5, 10, 15, 25, 30]
    everything = split_all_categories(demo, ["temperature", "gravity"], n_groups=2)
    print(everything)