from playlist_finder import query
import git
from pathlib import Path
import json
from re import search
from dotenv import load_dotenv
import os

load_dotenv()

# Global constants (can be accessed by run_main_logic)
USERS = {
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

USERS_TO_STORE = [
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

# Global variable for the repository, to be initialized in run_main_logic
# This allows mocks to target 'main.repo' if git.Repo.clone_from is patched.
repo = None

def run_main_logic():
    global repo # To assign to the global 'repo' variable
    overall_changes_made = False

    # Clone git repo
    remote = os.getenv("REMOTE") # os.getenv will be mocked in tests
    # git.Repo.clone_from will be mocked in tests to return a mock_repo_instance
    repo = git.Repo.clone_from(remote, "tmp")

    # repo is now the (mocked) repo instance
    with repo.config_writer() as git_config:
        git_config.set_value("user", "email", "operations@hisao.org")
        git_config.set_value("user", "name", "Playlist-Bot-Prod")

    # main.query will be mocked in tests
    results = query(USERS_TO_STORE)

    for user_id_from_query in results:
        user_has_playlist_changes = False
        # USERS is the global dictionary
        real_user_name = USERS[user_id_from_query]
        
        # pathlib.Path.mkdir will be mocked
        Path("tmp/" + real_user_name).mkdir(parents=True, exist_ok=True)
        original_plus_modded_names = {}
        
        for playlist_name_from_query in results[user_id_from_query]:
            if search("/", playlist_name_from_query):
                original_plus_modded_names[playlist_name_from_query] = playlist_name_from_query.replace("/", "-")
            else:
                original_plus_modded_names[playlist_name_from_query] = playlist_name_from_query

            file_name = (
                "tmp/"
                + real_user_name
                + "/"
                + original_plus_modded_names[playlist_name_from_query]
                + ".json"
            )
            
            # builtins.open will be mocked
            try:
                with open(file_name, "r") as f:
                    previous = json.load(f)
            except FileNotFoundError:
                previous = {}
                print("New playlist " + playlist_name_from_query)

            if previous != results[user_id_from_query][playlist_name_from_query]:
                print("Changes detected in " + real_user_name + "/" + playlist_name_from_query)
                with open(file_name, "w") as f:
                    json.dump(results[user_id_from_query][playlist_name_from_query], f, indent=4)
                
                # repo.index.add, repo.index.commit will be called on the mock_repo_instance
                repo.index.add(
                    [real_user_name + "/" + original_plus_modded_names[playlist_name_from_query] + ".json"]
                )
                user_has_playlist_changes = True
            else:
                print("No changes detected in " + real_user_name + "/" + playlist_name_from_query)

        if user_has_playlist_changes:
            print(f"Committing changes for {real_user_name}")
            repo.index.commit("Updating playlists for " + real_user_name)
            overall_changes_made = True

    if overall_changes_made:
        print("Pushing all changes to remote")
        # repo.remote().push will be called on the mock_repo_instance
        origin = repo.remote(name="origin")
        origin.push()

if __name__ == '__main__':
    run_main_logic()
