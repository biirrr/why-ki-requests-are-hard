"""Analysis of the annotation label counts."""

import json
from scipy import stats

CATEGORIES = ["books", "games", "movies"]


for category in CATEGORIES:
    print()
    print(category)
    scores = {"unsolved": [], "solved": [], "llm-solved": []}
    with open(f"data/annotated/{category}.json") as in_f:
        entries = json.load(in_f)
    for entry in entries:
        if "score" in entry["stats"]:
            scores[entry["data"]["category"]].append(entry["stats"]["score"])

    for key in ["unsolved", "solved", "llm-solved"]:
        print(
            "score",
            category,
            "&",
            key,
            "&",
            stats.quantile(scores[key], 0.25),
            "&",
            stats.quantile(scores[key], 0.5),
            "&",
            stats.quantile(scores[key], 0.75),
        )
        for key2 in ["unsolved", "solved", "llm-solved"]:
            if key != key2:
                wilcoxon = stats.ranksums(scores[key], scores[key2])
                print("      ", key2, wilcoxon.pvalue, wilcoxon.statistic)
        print()
    print("----")
    wilcoxon = stats.ranksums(
        scores["unsolved"], scores["solved"] + scores["llm-solved"]
    )
    print("combined", wilcoxon.pvalue, wilcoxon.statistic)
