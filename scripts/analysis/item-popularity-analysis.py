import json

from scipy import stats

CATEGORIES = ["books", "games", "movies"]

for category in CATEGORIES:
    with open(f"data/annotated/{category}.json") as in_f:
        entries = json.load(in_f)
    readinglog_count = {"solved": [], "llm-solved": []}
    for entry in entries:
        if (
            "readinglog_count" in entry["stats"]
            and entry["stats"]["readinglog_count"] != "NA"
            and entry["data"]["category"] in readinglog_count
        ):
            readinglog_count[entry["data"]["category"]].append(
                entry["stats"]["readinglog_count"]
            )
        if (
            "popularity_score" in entry["stats"]
            and entry["stats"]["popularity_score"] != "NA"
            and entry["data"]["category"] in readinglog_count
        ):
            readinglog_count[entry["data"]["category"]].append(
                entry["stats"]["popularity_score"]
            )
    for key in ["solved", "llm-solved"]:
        readinglog_count[key].sort()
        print(
            "total",
            category,
            "&",
            key,
            "&",
            readinglog_count[key][0],
            "&",
            stats.quantile(readinglog_count[key], 0.25),
            "&",
            stats.quantile(readinglog_count[key], 0.5),
            "&",
            stats.quantile(readinglog_count[key], 0.75),
            "&",
            readinglog_count[key][-1],
        )
    wilcoxon = stats.ranksums(
        readinglog_count["solved"], readinglog_count["llm-solved"]
    )
    print("      ", wilcoxon.pvalue, wilcoxon.statistic)
