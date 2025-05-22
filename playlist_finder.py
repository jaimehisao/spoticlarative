"""
This module is responsible for fetching playlist data from the Spotify API
using the spotipy library. It includes functions to query user playlists
and the tracks within those playlists.
"""
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from pprint import pprint
from dotenv import load_dotenv

load_dotenv()
auth_manager = SpotifyClientCredentials() # Not directly used for sp instance with OAuth, but kept for now.

# Define the scope of permissions needed from the Spotify API.
# This scope allows reading user's library, recently played, private/collaborative playlists, and followed artists/users.
scope = "user-library-read user-read-recently-played playlist-read-private playlist-read-collaborative user-follow-read"
sp = spotipy.Spotify(auth_manager=spotipy.SpotifyOAuth(scope=scope))

# Note: The existing block comment below seems to be an old note about file structure,
# which is now largely covered by the query function's docstring.
# It can be kept for historical context or removed if deemed redundant.
"""
Playlist store file structure

user
- playlist
-- playlist_id
-- total_tracks
-- {track_id, track_name, track_artist, track_album, track_duration, track_popularity, track_explicit, track_added_at, uri}


for each track we store 

- added_at date
- added_by username
- track_id
- artist_id main artist
- duration_ms
- populatiry 1-100



"""

# This function is currently unused in the main workflow.
def get_user_followers():
    results = sp.current_user_following_users()
    pprint(results)


def query(users_to_store: list[str]) -> dict:
    """
    Retrieves playlists and their tracks for a given list of Spotify user IDs.

    Args:
        users_to_store (list[str]): A list of Spotify user IDs whose playlists
                                    are to be fetched.

    Returns:
        dict: A nested dictionary structure.
              Top-level keys are user IDs.
              Each user ID maps to a dictionary of their playlists (keys are playlist names).
              Each playlist name maps to a dictionary containing:
                  'id' (str): The Spotify ID of the playlist.
                  'tracks' (list[dict]): A list of track dictionaries. Each track
                                         dictionary contains keys like `track_id`,
                                         `track_name`, `track_artist`, `track_album`,
                                         `track_duration`, `track_added_by`,
                                         `track_added_at`, `uri`.
    Example of return structure:
    {
        'user_id_1': {
            'Playlist Name 1': {
                'id': 'playlist_id_1',
                'tracks': [
                    {'track_id': 't1', 'track_name': 'Song A', ...},
                    {'track_id': 't2', 'track_name': 'Song B', ...}
                ]
            },
            # ... more playlists
        },
        'user_id_2': { ... }
    }
    """
    results_from_queries = {}
    # Iterate through each user ID provided.
    for user in users_to_store:
        results_from_queries[user] = {}

        # Fetch the first page of playlists for the current user.
        results = sp.user_playlists(user)
        playlists = results["items"]

        # Paginate through all playlists if there are more pages.
        while results['next']:
            results = sp.next(results) # Get the next page of playlists.
            playlists.extend(results['items'])

        # Iterate through the fetched playlists for the current user.
        for playlist in playlists:
            # Filter for playlists actually owned by the current user.
            if playlist["owner"]["id"] == user:
                results_from_queries[user][playlist["name"]] = {}
                results_from_queries[user][playlist["name"]]["id"] = playlist["id"]
                results_from_queries[user][playlist["name"]]["tracks"] = []
                
                # Fetch the first page of tracks for the current playlist.
                # 'fields="tracks,next"' limits the response to only track data and pagination info.
                playlist_tracks_results = sp.playlist(playlist["id"], fields="tracks,next") # Renamed to avoid conflict

                if "tracks" in playlist_tracks_results.keys():
                    tracks_data = playlist_tracks_results['tracks'] # Dedicated variable for track pagination data.
                    tracks = tracks_data['items']
                    
                    # Paginate through all tracks in the current playlist if there are more pages.
                    while tracks_data['next']:
                        tracks_data = sp.next(tracks_data) # Get the next page of tracks.
                        tracks.extend(tracks_data['items'])
                    
                    # Iterate through the fetched tracks for the current playlist.
                    for track in tracks:
                        # Try-except block to handle potential errors with individual track data.
                        # Some tracks might have missing fields or unexpected structures.
                        try:
                            # Construct a dictionary for the current track with relevant details.
                            tmp_track = {
                                "track_id": track["track"]["id"],               # Spotify ID of the track
                                "track_name": track["track"]["name"],             # Name of the track
                                "track_artist": track["track"]["artists"][0]["name"], # Primary artist of the track
                                "track_album": track["track"]["album"]["name"],   # Album of the track
                                "track_duration": track["track"]["duration_ms"],  # Duration of the track in milliseconds
                                "track_added_by": track["added_by"]["id"],      # User ID of who added the track
                                "track_added_at": track["added_at"],            # Timestamp when the track was added
                                "uri": track["track"]["uri"]                    # Spotify URI of the track
                            }
                            results_from_queries[user][playlist["name"]]["tracks"].append(tmp_track)
                        except (TypeError, KeyError, IndexError) as e:
                            # If an error occurs (e.g., a key is missing, or track['track'] is None),
                            # print an error message and the problematic track data, then continue.
                            print(f"Error processing track details. Exception: {type(e).__name__} - {e}")
                            print("Problematic track data:")
                            pprint(track)

    return results_from_queries
