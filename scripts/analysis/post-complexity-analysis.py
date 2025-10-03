"""Analysis of the post complexity."""

import json
from scipy import stats

CATEGORIES = ["books", "games", "movies"]


for category in CATEGORIES:
    print()
    print(category)
    character_lengths = {"unsolved": [], "solved": [], "llm-solved": []}
    word_lengths = {"unsolved": [], "solved": [], "llm-solved": []}
    readabilities = {"unsolved": [], "solved": [], "llm-solved": []}
    with open(f"data/annotated/{category}.json") as in_f:
        entries = json.load(in_f)
    for entry in entries:
        character_lengths[entry["data"]["category"]].append(
            entry["stats"]["full_post_length_chars"]
        )
        word_lengths[entry["data"]["category"]].append(
            entry["stats"]["full_post_length_words"]
        )
        readabilities[entry["data"]["category"]].append(
            entry["stats"]["full_post_readability"]
        )
    print("Character length")
    for key in ["unsolved", "solved", "llm-solved"]:
        print(
            category,
            "&",
            key,
            "&",
            stats.quantile(character_lengths[key], 0.25),
            "&",
            stats.quantile(character_lengths[key], 0.5),
            "&",
            stats.quantile(character_lengths[key], 0.75),
        )
    for key in ["unsolved", "solved", "llm-solved"]:
        for key2 in ["unsolved", "solved", "llm-solved"]:
            if key != key2:
                wilcoxon = stats.ranksums(
                    character_lengths[key], character_lengths[key2]
                )
                print("", key, key2, wilcoxon.pvalue, wilcoxon.statistic)
    print("Word length")
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
    for key in ["unsolved", "solved", "llm-solved"]:
        for key2 in ["unsolved", "solved", "llm-solved"]:
            if key != key2:
                wilcoxon = stats.ranksums(word_lengths[key], word_lengths[key2])
                print("", key, key2, wilcoxon.pvalue, wilcoxon.statistic)
    print("Readability")
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
    for key in ["unsolved", "solved", "llm-solved"]:
        for key2 in ["unsolved", "solved", "llm-solved"]:
            if key != key2:
                wilcoxon = stats.ranksums(readabilities[key], readabilities[key2])
                print("", key, key2, wilcoxon.pvalue, wilcoxon.statistic)
