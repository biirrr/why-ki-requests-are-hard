import json

from scipy import stats

CATEGORIES = ["books"]
for category in CATEGORIES:
    with open(f"data/annotated/{category}.json") as in_f:
        entries = json.load(in_f)
    first_publish_years = {"solved": [], "llm-solved": []}
    for entry in entries:
        if (
            "first_publish_year" in entry["stats"]
            and entry["stats"]["first_publish_year"] != "NA"
            and entry["data"]["category"] in first_publish_years
        ):
            first_publish_years[entry["data"]["category"]].append(
                entry["stats"]["first_publish_year"]
            )
    for key in ["solved", "llm-solved"]:
        first_publish_years[key].sort()
        print(
            "total",
            category,
            "&",
            key,
            "&",
            first_publish_years[key][0],
            "&",
            stats.quantile(first_publish_years[key], 0.25),
            "&",
            stats.quantile(first_publish_years[key], 0.5),
            "&",
            stats.quantile(first_publish_years[key], 0.75),
            "&",
            first_publish_years[key][-1],
        )
    wilcoxon = stats.ranksums(
        first_publish_years["solved"], first_publish_years["llm-solved"]
    )
    print("      ", wilcoxon.pvalue, wilcoxon.statistic)
