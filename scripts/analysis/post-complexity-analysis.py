"""Analysis of the post complexity."""

import json

from scipy import stats
from statsmodels.stats.multitest import multipletests

CATEGORIES = ["books", "games", "movies"]


for category in CATEGORIES:
    print()
    print(category)
    print("=" * len(category))
    word_lengths = {"unsolved": [], "solved": [], "llm-solved": []}
    readabilities = {"unsolved": [], "solved": [], "llm-solved": []}
    with open(f"data/annotated/{category}.json") as in_f:
        entries = json.load(in_f)
    for entry in entries:
        word_lengths[entry["data"]["category"]].append(
            entry["stats"]["full_post_length_words"]
        )
        readabilities[entry["data"]["category"]].append(
            entry["stats"]["full_post_readability"]
        )

    print("Word length\n-----------")
    for key in ["unsolved", "solved", "llm-solved"]:
        print(
            category,
            "&",
            key,
            "&",
            stats.quantile(word_lengths[key], 0.25),
            "&",
            stats.quantile(word_lengths[key], 0.5),
            "&",
            stats.quantile(word_lengths[key], 0.75),
        )
    tests = []
    for key in ["unsolved", "solved", "llm-solved"]:
        for key2 in ["unsolved", "solved", "llm-solved"]:
            if key != key2:
                wilcoxon = stats.ranksums(word_lengths[key], word_lengths[key2])
                tests.append((key, key2, wilcoxon.pvalue, wilcoxon.statistic))
    correction = multipletests([t[2] for t in tests])
    for test, corrected, reject in zip(tests, correction[1], correction[0]):
        print("", test[0], "->", test[1], corrected, reject)
    print()

    print("Readability\n----------")
    for key in ["unsolved", "solved", "llm-solved"]:
        print(
            category,
            "&",
            key,
            "&",
            stats.quantile(readabilities[key], 0.25),
            "&",
            stats.quantile(readabilities[key], 0.5),
            "&",
            stats.quantile(readabilities[key], 0.75),
        )
    tests = []
    for key in ["unsolved", "solved", "llm-solved"]:
        for key2 in ["unsolved", "solved", "llm-solved"]:
            if key != key2:
                wilcoxon = stats.ranksums(readabilities[key], readabilities[key2])
                tests.append((key, key2, wilcoxon.pvalue, wilcoxon.statistic))
    correction = multipletests([t[2] for t in tests])
    for test, corrected, reject in zip(tests, correction[1], correction[0]):
        print("", test[0], "->", test[1], corrected, reject)
