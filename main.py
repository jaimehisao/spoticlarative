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
repo = git.Repo.clone_from(remote, 'tmp')

with repo.config_writer() as git_config:
    git_config.set_value('user', 'email', 'operations@hisao.org')
    git_config.set_value('user', 'name', 'Playlist-Bot-Prod')

# Hisao, jojos, caro, anaoop, freddy, mario, thorsten, stevie
users_to_store = ["jaimehisao",
                  "marijojos99",
                  "1279908833",  # caro
                  "analaurdzz",
                  "1293929854",  # freddy
                  "mariomoo",
                  "11131420233",  # thotta
                  "1292030678",  # stevie
                  "1283325282"  # bruno
                  ]

results = query(users_to_store)

for user in results:
    Path("tmp/" + user).mkdir(parents=True, exist_ok=True)
    original_plus_modded_names = {}
    for playlist in results[user]:

        if search("/", playlist):
            original_plus_modded_names[playlist] = playlist.replace("/", "-")
        else:
            original_plus_modded_names[playlist] = playlist
            """
            tmp = playlist
            del results[user][playlist]
            playlist = playlist.replace("/", "-")
            results[user][playlist] = tmp
            """

        file_name = "tmp/" + user + "/" + original_plus_modded_names[playlist] + ".json"

        try:
            with open(file_name, "r") as f:
                previous = json.load(f)
        except FileNotFoundError:
            previous = {}
            print("New playlist" + playlist)

        if previous != results[user][playlist]:
            print("Changes detected in " + user + "/" + playlist)
            with open(file_name, "w") as f:
                json.dump(results[user][playlist], f, indent=4)
            repo.index.add([user + "/" + original_plus_modded_names[playlist] + ".json"])
            repo.index.commit("Updating playlists for " + user)
            origin = repo.remote(name='origin')
            origin.push()
        else:
            print("No changes detected in " + user + "/" + playlist)

    # repo.git.add('--all')
    # count_modified_files = len(repo.remote("origin").repo.index.diff("HEAD"))
    # count_staged_files = len(repo.index.diff("HEAD"))
    # print(count_modified_files, count_staged_files)

    # repo.git.add(all=True)
    # repo.index.commit("Updated playlists for user: " + user)
    # repo.remotes.origin.push()
