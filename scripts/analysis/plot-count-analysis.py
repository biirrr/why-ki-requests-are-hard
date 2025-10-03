"""Analysis of the plot counts."""

import json
from scipy import stats

CATEGORIES = ["books", "games", "movies"]


for category in CATEGORIES:
    print()
    print(category)
    plot_counts = {"unsolved": 0, "solved": 0, "llm-solved": 0}
    with open(f"data/annotated/{category}.json") as in_f:
        entries = json.load(in_f)
    for entry in entries:
        if entry["stats"]["has_plot"]:
            plot_counts[entry["data"]["category"]] = (
                plot_counts[entry["data"]["category"]] + 1
            )
    for key in ["unsolved", "solved", "llm-solved"]:
        print(category, "&", key, "&", plot_counts[key])
        for key2 in ["unsolved", "solved", "llm-solved"]:
            if key != key2:
                chi2 = stats.chi2_contingency(
                    [
                        [plot_counts[key], 50 - plot_counts[key]],
                        [plot_counts[key2], 50 - plot_counts[key2]],
                    ]
                )
                print("", key2, chi2.pvalue, chi2.statistic)
    print("-----")
    chi2 = stats.chi2_contingency(
        [
            [plot_counts["unsolved"], 50 - plot_counts["unsolved"]],
            [
                plot_counts["solved"] + plot_counts["llm-solved"],
                100 - plot_counts["solved"] - plot_counts["llm-solved"],
            ],
        ]
    )
    print("", "shared-plot-count", chi2.pvalue, chi2.statistic)
    print("-----")

    plot_character_lengths = {"unsolved": [], "solved": [], "llm-solved": []}
    plot_word_lengths = {"unsolved": [], "solved": [], "llm-solved": []}
    for entry in entries:
        if entry["stats"]["plot_character_length"] > 0:
            plot_character_lengths[entry["data"]["category"]].append(
                entry["stats"]["plot_character_length"]
            )
        if entry["stats"]["plot_word_length"] > 0:
            plot_word_lengths[entry["data"]["category"]].append(
                entry["stats"]["plot_word_length"]
            )
    for key in ["unsolved", "solved", "llm-solved"]:
        print(
            "character",
            category,
            "&",
            key,
            "&",
            stats.quantile(plot_character_lengths[key], 0.25),
            "&",
            stats.quantile(plot_character_lengths[key], 0.5),
            "&",
            stats.quantile(plot_character_lengths[key], 0.75),
        )
        for key2 in ["unsolved", "solved", "llm-solved"]:
            if key != key2:
                wilcoxon = stats.ranksums(
                    plot_character_lengths[key], plot_character_lengths[key2]
                )
                print("", key2, wilcoxon.pvalue, wilcoxon.statistic)
        print(
            "word",
            category,
            "&",
            key,
            "&",
            stats.quantile(plot_word_lengths[key], 0.25),
            "&",
            stats.quantile(plot_word_lengths[key], 0.5),
            "&",
            stats.quantile(plot_word_lengths[key], 0.75),
        )
        for key2 in ["unsolved", "solved", "llm-solved"]:
            if key != key2:
                wilcoxon = stats.ranksums(
                    plot_word_lengths[key], plot_word_lengths[key2]
                )
                print("", key2, wilcoxon.pvalue, wilcoxon.statistic)
