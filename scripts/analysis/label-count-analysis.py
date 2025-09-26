"""Analysis of the annotation label counts."""

import json
from scipy import stats

CATEGORIES = ["books", "games", "movies"]


for category in CATEGORIES:
    print()
    print(category)
    total_labels = {"unsolved": [], "solved": [], "llm-solved": []}
    total_unique_labels = {"unsolved": [], "solved": [], "llm-solved": []}
    with open(f"data/annotated/{category}.json") as in_f:
        entries = json.load(in_f)
    for entry in entries:
        total_labels[entry["data"]["category"]].append(entry["stats"]["total_labels"])
        total_unique_labels[entry["data"]["category"]].append(
            entry["stats"]["total_unique_labels"]
        )

    for key in ["unsolved", "solved", "llm-solved"]:
        print(
            "total",
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
        for key2 in ["unsolved", "solved", "llm-solved"]:
            if key != key2:
                wilcoxon = stats.ranksums(total_labels[key], total_labels[key2])
                print("      ", key2, wilcoxon.pvalue, wilcoxon.statistic)
        print(
            "total unique",
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
        for key2 in ["unsolved", "solved", "llm-solved"]:
            if key != key2:
                wilcoxon = stats.ranksums(
                    total_unique_labels[key], total_unique_labels[key2]
                )
                print("             ", key2, wilcoxon.pvalue, wilcoxon.statistic)
