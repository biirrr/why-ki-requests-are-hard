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


genre_cache = {}


def get_game(game_id: str) -> dict | None:
    """Fetch the data for a single game."""
    sleep(0.3)
    with Client(timeout=30) as client:
        response = client.post(
            "https://id.twitch.tv/oauth2/token",
            params=[
                ("client_id", os.environ["IGDB_ID"]),
                ("client_secret", os.environ["IGDB_SECRET"]),
                ("grant_type", "client_credentials"),
            ],
        )
        if response.status_code == 200:  # noqa: PLR2004
            auth_data = response.json()
            response = client.post(
                "https://api.igdb.com/v4/games",
                headers=[
                    ("Client-ID", os.environ["IGDB_ID"]),
                    ("Authorization", f"Bearer {auth_data['access_token']}"),
                    ("Accept", "application/json"),
                ],
                data=f"fields id,name,release_dates,url,parent_game,genres;limit 100;where id = {game_id};",
            )
            results = response.json()
            for entry in results:
                if "release_dates" in entry:
                    sleep(0.3)
                    response = client.post(
                        "https://api.igdb.com/v4/release_dates",
                        headers=[
                            ("Client-ID", os.environ["IGDB_ID"]),
                            ("Authorization", f"Bearer {auth_data['access_token']}"),
                            ("Accept", "application/json"),
                        ],
                        data=f"fields y;limit 100;where id = ({','.join([str(v) for v in entry['release_dates']])});",
                    )
                    dates = response.json()
                    entry["release_years"] = list(
                        {date["y"] for date in dates if "y" in date}
                    )
                else:
                    entry["release_years"] = []
            if len(results) == 1:
                sleep(0.3)
                response = client.post(
                    "https://api.igdb.com/v4/popularity_primitives",
                    headers=[
                        ("Client-ID", os.environ["IGDB_ID"]),
                        ("Authorization", f"Bearer {auth_data['access_token']}"),
                        ("Accept", "application/json"),
                    ],
                    data=f"fields game_id,value,popularity_type;limit 100;where game_id = {game_id};",
                )
                popularity_results = response.json()
                popularity_score = 0
                for pop_result in popularity_results:
                    if pop_result["popularity_type"] in [2, 3, 4]:
                        popularity_score = popularity_score + pop_result["value"]
                results[0]["popularity_score"] = popularity_score
                genre_popularities = [0]
                if "genres" in results[0]:
                    for genre_id in results[0]["genres"]:
                        sleep(0.3)
                        response = client.post(
                            "https://api.igdb.com/v4/multiquery",
                            headers=[
                                ("Client-ID", os.environ["IGDB_ID"]),
                                (
                                    "Authorization",
                                    f"Bearer {auth_data['access_token']}",
                                ),
                                ("Accept", "application/json"),
                            ],
                            data='query games/count "Count of Games" { where genres='
                            + str(genre_id)
                            + " ; };",
                        )
                        tmp_result = response.json()
                        if "count" in tmp_result[0]:
                            genre_popularities.append(tmp_result[0]["count"])
                        else:
                            print(tmp_result)
                results[0]["genre_popularity"] = max(genre_popularities)
                return results[0]

    return None


with open("data/annotated/games.json") as in_f:
    entries = json.load(in_f)

for entry in entries:
    if entry["data"]["category"] == "unsolved":
        continue
    with open("data/games/games-threads.tsv") as in_f:
        reader = csv.DictReader(in_f, delimiter="\t")
        for line in reader:
            if str(entry["data"]["thread_id"]) == str(line["thread_id"]):
                if line["answer"] != "" and line["IGDB_id"] and line["IGDB_id"] != "":
                    game = get_game(line["IGDB_id"])
                    if game is not None:
                        if "release_years" in game and len(game["release_years"]) > 0:
                            entry["stats"]["first_publish_year"] = game[
                                "release_years"
                            ][0]
                        entry["stats"]["popularity_score"] = game["popularity_score"]
                        entry["stats"]["genre_popularity"] = game["genre_popularity"]

with open("data/annotated/games.json", "w") as out_f:
    json.dump(entries, out_f)
