"""Generate basic stats from the annotations."""

import csv
import json

CATEGORIES = ["books"]
STATS_FILENAMES = {
    "books": "data/books/book_answers-popularity.tsv",
}
STATS_KEYS = ["readinglog_count", "first_publish_year", "genre_popularity"]


for category in CATEGORIES:
    with open(f"data/annotated/{category}.json") as in_f:
        entries = json.load(in_f)
    with open(STATS_FILENAMES[category]) as in_f:
        reader = csv.DictReader(in_f, delimiter="\t")
        for line in reader:
            for entry in entries:
                if str(line["thread_id"]) == str(entry["data"]["thread_id"]):
                    if "stats" not in entry:
                        entry["stats"] = {}
                    for key in STATS_KEYS:
                        if line[key] == "NA" or line[key] == "":
                            entry["stats"][key] = "NA"
                        else:
                            entry["stats"][key] = float(line[key])
    with open(f"data/annotated/{category}.json", "w") as out_f:
        json.dump(entries, out_f)
