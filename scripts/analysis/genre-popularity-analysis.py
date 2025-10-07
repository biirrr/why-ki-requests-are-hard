import json

from scipy import stats

CATEGORIES = ["books", "games", "movies"]

for category in CATEGORIES:
    with open(f"data/annotated/{category}.json") as in_f:
        entries = json.load(in_f)
    genre_popularity = {"solved": [], "llm-solved": []}
    for entry in entries:
        if (
            "genre_popularity" in entry["stats"]
            and entry["stats"]["genre_popularity"] != "NA"
            and entry["data"]["category"] in genre_popularity
        ):
            genre_popularity[entry["data"]["category"]].append(
                entry["stats"]["genre_popularity"]
            )
    for key in ["solved", "llm-solved"]:
        genre_popularity[key].sort()
        print(
            "total",
            category,
            "&",
            key,
            "&",
            genre_popularity[key][0],
            "&",
            stats.quantile(genre_popularity[key], 0.25),
            "&",
            stats.quantile(genre_popularity[key], 0.5),
            "&",
            stats.quantile(genre_popularity[key], 0.75),
            "&",
            genre_popularity[key][-1],
        )
    wilcoxon = stats.ranksums(
        genre_popularity["solved"], genre_popularity["llm-solved"]
    )
    print("      ", wilcoxon.pvalue, wilcoxon.statistic)
