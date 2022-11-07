import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from pprint import pprint

auth_manager = SpotifyClientCredentials()
# sp = spotipy.Spotify(auth_manager=auth_manager)
scope = "user-library-read user-read-recently-played playlist-read-private playlist-read-collaborative user-follow-read"
sp = spotipy.Spotify(auth_manager=spotipy.SpotifyOAuth(scope=scope))

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


def get_user_followers():

    results = sp.current_user_following_users()
    pprint(results)


def query(users_to_store: [str]):
    results_from_queries = {}
    for user in users_to_store:
        results_from_queries[user] = {}

        results = sp.user_playlists(user)
        playlists = results["items"]

        while results['next']:
            results = sp.next(results)
            playlists.extend(results['items'])

        for playlist in playlists:
            if playlist["owner"]["id"] == user:
                results_from_queries[user][playlist["name"]] = {}
                results_from_queries[user][playlist["name"]]["id"] = playlist["id"]
                results_from_queries[user][playlist["name"]]["tracks"] = []
                results = sp.playlist(playlist["id"], fields="tracks,next")

                if "tracks" in results.keys():
                    tracks = results['tracks']['items']
                    while "tracks" in results.keys() and results['tracks']['next']:
                        results = sp.next(results['tracks'])
                        tracks.extend(results['items'])

                        if results['next']:
                            results = sp.next(results)
                            tracks.extend(results['items'])

                    for track in tracks:
                        try:
                            tmp_track = {"track_id": track["track"]["id"],
                                         "track_name": track["track"]["name"],
                                         "track_artist": track["track"]["artists"][0]["name"],
                                         "track_album": track["track"]["album"]["name"],
                                         "track_duration": track["track"]["duration_ms"],
                                         "track_popularity": track["track"]["popularity"],
                                         "track_added_by": track["added_by"]["id"], "track_added_at": track["added_at"],
                                         "uri": track["track"]["uri"]}
                            results_from_queries[user][playlist["name"]]["tracks"].append(tmp_track)
                        except Exception:
                            print("Error with track")
                            print(track)
                            print("Error with track")

    return results_from_queries
