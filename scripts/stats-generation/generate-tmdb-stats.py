# SPDX-FileCopyrightText: 2024-present Mark Hall <mark.hall@work.room3b.eu>
#
# SPDX-License-Identifier: MIT
"""IGDB API functions."""

import csv
import json
import os

from enum import Enum
from time import sleep

from httpx import Client


def get_movie(imdb_id: str):
    with Client(timeout=30) as client:
        response = client.get(
            f"https://api.themoviedb.org/3/find/{imdb_id}?external_source=imdb_id",
            headers=[
                ("Authorization", f"Bearer {os.environ['TMDB_TOKEN']}"),
                ("Accept", "application/json"),
            ],
        )
        if response.status_code == 200:
            return response.json()["movie_results"][0]
    return None


with open("data/annotated/movies.json") as in_f:
    entries = json.load(in_f)

for entry in entries:
    if entry["data"]["category"] == "unsolved":
        continue
    with open("data/movies/movies-threads.tsv") as in_f:
        reader = csv.DictReader(in_f, delimiter="\t")
        for line in reader:
            if str(entry["data"]["thread_id"]) == str(line["thread_id"]):
                if line["answer"] != "" and line["IMDB_id"] and line["IMDB_id"] != "":
                    movie = get_movie(line["IMDB_id"])
                    if movie is not None:
                        if "release_date" in movie:
                            entry["stats"]["first_publish_year"] = int(
                                movie["release_date"][0:4]
                            )
                        entry["stats"]["popularity_score"] = movie["popularity"]

with open("data/annotated/movies.json", "w") as out_f:
    json.dump(entries, out_f)
