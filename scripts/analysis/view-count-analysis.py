"""Analysis of the annotation label counts."""

import json

from scipy import stats
from statsmodels.stats.multitest import multipletests

CATEGORIES = ["books", "games", "movies"]


for category in CATEGORIES:
    print()
    print(category)
    print("=" * len(category))
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
    tests = []
    for key in ["unsolved", "solved", "llm-solved"]:
        for key2 in ["unsolved", "solved", "llm-solved"]:
            if key != key2:
                wilcoxon = stats.ranksums(scores[key], scores[key2])
                tests.append((key, key2, wilcoxon.pvalue, wilcoxon.statistic))
    correction = multipletests([t[2] for t in tests])
    for test, corrected, reject in zip(tests, correction[1], correction[0]):
        print("", test[0], "->", test[1], corrected, reject)

    wilcoxon = stats.ranksums(
        scores["unsolved"], scores["solved"] + scores["llm-solved"]
    )
    print(
        "", "unsolved", "->", "solved+llm-solved", wilcoxon.pvalue, wilcoxon.statistic
    )
