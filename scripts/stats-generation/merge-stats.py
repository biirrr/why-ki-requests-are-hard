"""Generate basic stats from the annotations."""

import csv
import json

CATEGORIES = ["books", "games", "movies"]
STATS_FILENAMES = {
    "books": "data/annotated/statistics.books.reddit-spring+summer2025.tsv",
    "games": "data/annotated/statistics.games.reddit-spring2025.tsv",
    "movies": "data/annotated/statistics.movies.reddit-spring2025.tsv",
}
STATS_KEYS = [
    "title_length_chars",
    "text_length_chars",
    "full_post_length_chars",
    "title_length_words",
    "text_length_words",
    "full_post_length_words",
    "title_readability",
    "text_readability",
    "full_post_readability",
    "reply_counter",
    "replies_until_solved",
    "replies_until_confirmed",
    "OP_reply_count",
    "OP_reply_count_before_confirmed",
    "solved_by_OP",
    "unique_user_replies",
    "unique_user_count",
    "score",
]

for category in CATEGORIES:
    with open(f"data/annotated/{category}.json") as in_f:
        entries = json.load(in_f)
    with open(STATS_FILENAMES[category]) as in_f:
        reader = csv.DictReader(in_f, delimiter="\t")
        for line in reader:
            for entry in entries:
                if line["thread_id"] == entry["data"]["thread_id"]:
                    if "stats" not in entry:
                        entry["stats"] = {}
                    for key in STATS_KEYS:
                        if line[key] == "NA":
                            entry["stats"][key] = "NA"
                        else:
                            entry["stats"][key] = float(line[key])
    with open(f"data/annotated/{category}.json", "w") as out_f:
        json.dump(entries, out_f)
