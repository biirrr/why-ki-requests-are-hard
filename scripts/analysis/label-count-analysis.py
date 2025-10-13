"""Analysis of the annotation label counts."""

import json

from scipy import stats
from statsmodels.stats.multitest import multipletests

CATEGORIES = ["books", "games", "movies"]


for category in CATEGORIES:
    print()
    print(category)
    print("=" * len(category))

    total_labels = {"unsolved": [], "solved": [], "llm-solved": []}
    total_unique_labels = {"unsolved": [], "solved": [], "llm-solved": []}
    with open(f"data/annotated/{category}.json") as in_f:
        entries = json.load(in_f)
    for entry in entries:
        total_labels[entry["data"]["category"]].append(entry["stats"]["total_labels"])
        total_unique_labels[entry["data"]["category"]].append(
            entry["stats"]["total_unique_labels"]
        )

    print("Total labels\n------------")
    for key in ["unsolved", "solved", "llm-solved"]:
        print(
            category,
            "&",
            key,
            "&",
            stats.quantile(total_labels[key], 0.25),
            "&",
            stats.quantile(total_labels[key], 0.5),
            "&",
            stats.quantile(total_labels[key], 0.75),
        )
    tests = []
    for key in ["unsolved", "solved", "llm-solved"]:
        for key2 in ["unsolved", "solved", "llm-solved"]:
            if key != key2:
                wilcoxon = stats.ranksums(total_labels[key], total_labels[key2])
                tests.append((key, key2, wilcoxon.pvalue, wilcoxon.statistic))
    correction = multipletests([t[2] for t in tests])
    for test, corrected, reject in zip(tests, correction[1], correction[0]):
        print("", test[0], "->", test[1], corrected, reject)
    print()

    print("Total unique labels\n-------------------")
    for key in ["unsolved", "solved", "llm-solved"]:
        print(
            category,
            "&",
            key,
            "&",
            stats.quantile(total_unique_labels[key], 0.25),
            "&",
            stats.quantile(total_unique_labels[key], 0.5),
            "&",
            stats.quantile(total_unique_labels[key], 0.75),
        )
    tests = []
    for key in ["unsolved", "solved", "llm-solved"]:
        for key2 in ["unsolved", "solved", "llm-solved"]:
            if key != key2:
                wilcoxon = stats.ranksums(
                    total_unique_labels[key], total_unique_labels[key2]
                )
                tests.append((key, key2, wilcoxon.pvalue, wilcoxon.statistic))
    correction = multipletests([t[2] for t in tests])
    for test, corrected, reject in zip(tests, correction[1], correction[0]):
        print("", test[0], "->", test[1], corrected, reject)
