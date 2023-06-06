from playlist_finder import query
import git
from pathlib import Path
import json
from re import search
from dotenv import load_dotenv
import os

load_dotenv()

# Clone git repo
remote = os.getenv("REMOTE")
repo = git.Repo.clone_from(remote, "tmp")

with repo.config_writer() as git_config:
    git_config.set_value("user", "email", "operations@hisao.org")
    git_config.set_value("user", "name", "Playlist-Bot-Prod")

users = {
    "jaimehisao": "jaimehisao",
    "marijojos99": "marijojos99",
    "1279908833": "caro",
    "analaurdzz": "analaurdzz",
    "1293929854": "freddy",
    "mariomoo": "mariomoo",
    "11131420233": "thotta",
    "1292030678": "stevie",
    "1283325282": "bruno",
    "anazerm28": "anazerm28",
    "aroquev00": "aroquev00",
    "1291740798": "marin",
}

users_to_store = [
    "jaimehisao",
    "marijojos99",
    "1279908833",  # caro
    "analaurdzz",
    "1293929854",  # freddy
    "mariomoo",
    "11131420233",  # thotta
    "1292030678",  # stevie
    "1283325282",  # bruno
    "anazerm28",
]

results = query(users_to_store)

changes_detected = False

for user in results:
    real_user_name = users[user]
    Path("tmp/" + real_user_name).mkdir(parents=True, exist_ok=True)
    original_plus_modded_names = {}
    for playlist in results[user]:
        if search("/", playlist):
            original_plus_modded_names[playlist] = playlist.replace("/", "-")
        else:
            original_plus_modded_names[playlist] = playlist

        file_name = (
            "tmp/"
            + real_user_name
            + "/"
            + original_plus_modded_names[playlist]
            + ".json"
        )

        try:
            with open(file_name, "r") as f:
                previous = json.load(f)
        except FileNotFoundError:
            previous = {}
            print("New playlist " + playlist)

        changes_detected = False

        if previous != results[user][playlist]:
            print("Changes detected in " + real_user_name + "/" + playlist)
            with open(file_name, "w") as f:
                json.dump(results[user][playlist], f, indent=4)
            repo.index.add(
                [real_user_name + "/" + original_plus_modded_names[playlist] + ".json"]
            )
            repo.index.commit("Updating playlists for " + real_user_name)
            changes_detected = True
        else:
            print("No changes detected in " + real_user_name + "/" + playlist)
    if changes_detected:
        repo.index.commit("Updating playlists for " + real_user_name)
        origin = repo.remote(name="origin")
        origin.push()
