"""
Main script for Spoticlarative.

This script serves as the main entry point for an application that fetches
Spotify playlists for a predefined list of users, stores these playlists as
JSON files, and versions them using a Git repository. It tracks changes
to playlists over time by committing updates to the repository.
"""
from playlist_finder import query
import git
from pathlib import Path
import json
from re import search
from dotenv import load_dotenv
import os

# Load environment variables from a .env file (if present)
# This is typically used for sensitive information like API keys or remote Git URLs.
load_dotenv()

# Global constants defining user mappings and the list of users to process.
# USERS: Maps Spotify user IDs (which can be non-human-readable) to desired directory/commit names.
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

# USERS_TO_STORE: A list of Spotify user IDs whose playlists will be fetched and stored.
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

# Global variable for the Git repository instance.
# It's initialized within run_main_logic() after cloning.
# This allows mocks to target 'main.repo' if git.Repo.clone_from is patched during tests.
repo = None

def run_main_logic():
    """
    Executes the core logic of the application.

    This includes:
    1. Cloning a remote Git repository to a local 'tmp' directory.
    2. Configuring Git user details for commits.
    3. Fetching playlist data for specified users using `playlist_finder.query`.
    4. Processing each user's playlists:
        - Creating user-specific directories if they don't exist.
        - Sanitizing playlist names for use as filenames.
        - Reading existing playlist data from JSON files (if any).
        - Comparing new data with existing data to detect changes.
        - Writing updated playlist data to JSON files.
        - Staging changed files in Git.
    5. Committing changes per user if any of their playlists were updated.
    6. Pushing all committed changes to the remote repository if any overall changes were made.
    """
    global repo # Allow assignment to the global 'repo' variable.
    overall_changes_made = False # Flag to track if any changes were made across all users.

    # Retrieve the remote Git repository URL from environment variables.
    remote_url = os.getenv("REMOTE")
    # Clone the remote repository into a local directory named "tmp".
    # The 'repo' variable will hold the GitPython Repo object.
    repo = git.Repo.clone_from(remote_url, "tmp")

    # Configure Git user email and name for commits made by this script.
    # This uses a context manager for safe configuration writing.
    with repo.config_writer() as git_config:
        git_config.set_value("user", "email", "operations@hisao.org")
        git_config.set_value("user", "name", "Playlist-Bot-Prod")

    # Fetch playlist data for the users defined in USERS_TO_STORE.
    # 'results' will be a dictionary where keys are user IDs and values are their playlist data.
    results = query(USERS_TO_STORE)

    # Main processing loop: Iterate through each user whose playlists were fetched.
    for user_id_from_query in results:
        user_has_playlist_changes = False # Flag for changes specific to the current user.
        # Map the user ID from the query (potentially a Spotify ID) to a human-readable name.
        real_user_name = USERS[user_id_from_query]
        
        # Create a directory for the current user inside "tmp/" if it doesn't already exist.
        # parents=True creates parent directories if needed; exist_ok=True doesn't raise error if dir exists.
        Path("tmp/" + real_user_name).mkdir(parents=True, exist_ok=True)
        original_plus_modded_names = {} # Stores original and sanitized playlist names.
        
        # Playlist processing loop: Iterate through each playlist of the current user.
        for playlist_name_from_query in results[user_id_from_query]:
            # Sanitize playlist names that contain slashes, replacing them with hyphens
            # to ensure valid filenames.
            if search("/", playlist_name_from_query):
                original_plus_modded_names[playlist_name_from_query] = playlist_name_from_query.replace("/", "-")
            else:
                original_plus_modded_names[playlist_name_from_query] = playlist_name_from_query

            # Construct the full path for the playlist's JSON file.
            file_name = (
                "tmp/"
                + real_user_name
                + "/"
                + original_plus_modded_names[playlist_name_from_query]
                + ".json"
            )
            
            # Try to read the existing playlist data from its JSON file.
            try:
                with open(file_name, "r") as f:
                    previous = json.load(f)
            # If the file is not found, it means this is a new playlist.
            except FileNotFoundError:
                previous = {} # Initialize 'previous' as empty for new playlists.
                print("New playlist " + playlist_name_from_query)

            # Compare the previously stored playlist data with the newly fetched data.
            if previous != results[user_id_from_query][playlist_name_from_query]:
                print("Changes detected in " + real_user_name + "/" + playlist_name_from_query)
                # If changes are detected, write the new playlist data to the JSON file.
                # json.dump writes the data with an indent for pretty printing.
                with open(file_name, "w") as f:
                    json.dump(results[user_id_from_query][playlist_name_from_query], f, indent=4)
                
                # Stage the changed (or new) playlist file in Git.
                repo.index.add(
                    [real_user_name + "/" + original_plus_modded_names[playlist_name_from_query] + ".json"]
                )
                user_has_playlist_changes = True # Mark that this user had changes.
            else:
                print("No changes detected in " + real_user_name + "/" + playlist_name_from_query)

        # If any of the current user's playlists were changed (or are new), commit these changes.
        if user_has_playlist_changes:
            print(f"Committing changes for {real_user_name}")
            repo.index.commit("Updating playlists for " + real_user_name)
            overall_changes_made = True # Mark that at least one user had changes.

    # If any changes were made across all users and committed, push them to the remote repository.
    if overall_changes_made:
        print("Pushing all changes to remote")
        origin = repo.remote(name="origin") # Get the 'origin' remote.
        origin.push() # Push the changes.

# Standard Python idiom: Call run_main_logic() only when the script is executed directly.
if __name__ == '__main__':
    run_main_logic()
