"""Generate basic stats from the annotations."""

import json

CATEGORIES = ["books", "games", "movies"]
UNIQUE_LABELS = {
    "Properties",
    "Connectivity",
    "Not this one",
    "Setting",
    "Dialogue and lyrics",
    "Search history",
    "Link to external resource",
    "Soundtrack",
    "World building",
    "Time",
    "Impact",
    "Contributor(s)",
    "Perspective",
    "Genre",
    "Plot",
    "Context",
    "Publisher",
    "Comprehensiveness",
    "N/A",
    "Cutscene(s)",
    "Graphic design",
    "Collection, series or franchise",
    "Character(s)",
    "Novelty",
    "Version",
    "Topic",
    "Language",
    "Popularity",
    "Expandability",
    "Title",
    "Supplementary material",
    "(Re)play value",
    "Situation of exposure",
    "Audience",
    "Availability",
    "Structure",
    "Mood",
    "Game mode",
    "Controls",
    "Sound design",
    "Release date",
    "Gameplay mechanics",
    "Accessibility",
}

for category in CATEGORIES:
    with open(f"data/annotated/{category}.json") as in_f:
        entries = json.load(in_f)
    for entry in entries:
        labels = []
        plot_character_length = 0
        plot_word_length = 0
        for annotation in entry["annotations"][0]["result"]:
            labels.extend(annotation["value"]["labels"])
            if "Plot" in annotation["value"]["labels"]:
                plot_character_length = plot_character_length + len(
                    annotation["value"]["text"]
                )
                plot_word_length = plot_word_length + len(
                    annotation["value"]["text"].split(" ")
                )
        if "stats" not in entry:
            entry["stats"] = {}
        entry["stats"]["total_labels"] = len(labels)
        entry["stats"]["total_unique_labels"] = len(set(labels))
        entry["stats"]["has_plot"] = "Plot" in labels
        entry["stats"]["plot_character_length"] = plot_character_length
        entry["stats"]["plot_word_length"] = plot_word_length
    with open(f"data/annotated/{category}.json", "w") as out_f:
        json.dump(entries, out_f)
