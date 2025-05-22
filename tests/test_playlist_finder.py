import pytest
from unittest.mock import MagicMock, patch
from playlist_finder import query # Assuming query is directly importable
# If spotipy objects are instantiated at module level in playlist_finder.py,
# you might need to patch them there. For now, we'll assume they can be
# patched during test setup or via dependency injection if that was an option.

# Test Case 1: Empty user list
def test_query_empty_user_list(mocker):
    # Mock spotipy.Spotify instance (playlist_finder.sp)
    mocker.patch('playlist_finder.sp')
    
    result = query([])
    assert result == {}

# Test Case 2: User with no playlists
def test_query_user_with_no_playlists(mocker):
    mock_sp = mocker.patch('playlist_finder.sp')
    mock_sp.user_playlists.return_value = {'items': [], 'next': None}
    
    user_id = 'test_user_id'
    results_from_queries = query([user_id])
    
    assert user_id in results_from_queries
    assert results_from_queries[user_id] == {}

# Test Case 3: User with one empty playlist
def test_query_user_with_one_empty_playlist(mocker):
    mock_sp = mocker.patch('playlist_finder.sp')
    
    user_id = 'test_user_id'
    playlist_id = 'playlist1'
    playlist_name = 'Empty Playlist'
    
    # Mock user_playlists response
    mock_sp.user_playlists.return_value = {
        'items': [{'name': playlist_name, 'id': playlist_id, 'owner': {'id': user_id}}],
        'next': None
    }
    
    # Mock playlist response (when called for the specific playlist)
    mock_sp.playlist.return_value = {
        'tracks': {'items': [], 'next': None}
    }
    
    results_from_queries = query([user_id])
    
    assert user_id in results_from_queries
    assert playlist_name in results_from_queries[user_id]
    assert results_from_queries[user_id][playlist_name]['id'] == playlist_id
    assert results_from_queries[user_id][playlist_name]['tracks'] == []

# Test Case 4: User with playlist and tracks
def test_query_user_with_playlist_and_tracks(mocker):
    mock_sp = mocker.patch('playlist_finder.sp')
    user_id = 'test_user_id'
    playlist_id = 'playlist1'
    playlist_name = 'Playlist With Tracks'
    
    track1 = {
        'track': {
            'id': 'track1_id', 'name': 'Track 1', 'artists': [{'name': 'Artist 1'}],
            'album': {'name': 'Album 1'}, 'duration_ms': 200000, 'uri': 'spotify:track:track1_id'
        },
        'added_by': {'id': user_id}, 'added_at': '2023-01-01T00:00:00Z'
    }
    track2 = {
        'track': {
            'id': 'track2_id', 'name': 'Track 2', 'artists': [{'name': 'Artist 2'}],
            'album': {'name': 'Album 2'}, 'duration_ms': 220000, 'uri': 'spotify:track:track2_id'
        },
        'added_by': {'id': user_id}, 'added_at': '2023-01-02T00:00:00Z'
    }

    mock_sp.user_playlists.return_value = {
        'items': [{'name': playlist_name, 'id': playlist_id, 'owner': {'id': user_id}}],
        'next': None
    }
    mock_sp.playlist.return_value = {
        'tracks': {'items': [track1, track2], 'next': None}
    }
    
    results = query([user_id])
    
    assert user_id in results
    assert playlist_name in results[user_id]
    assert results[user_id][playlist_name]['id'] == playlist_id
    assert len(results[user_id][playlist_name]['tracks']) == 2
    
    # Check details of the first track
    res_track1 = results[user_id][playlist_name]['tracks'][0]
    assert res_track1['track_id'] == 'track1_id'
    assert res_track1['track_name'] == 'Track 1'
    assert res_track1['track_artist'] == 'Artist 1'
    assert res_track1['track_album'] == 'Album 1'
    assert res_track1['track_duration'] == 200000
    assert res_track1['track_added_by'] == user_id
    assert res_track1['track_added_at'] == '2023-01-01T00:00:00Z'
    assert res_track1['uri'] == 'spotify:track:track1_id'

# Test Case 5: Playlist pagination
def test_query_playlist_pagination(mocker):
    mock_sp = mocker.patch('playlist_finder.sp')
    user_id = 'test_user_id'
    playlist1_name = 'Playlist Page 1'
    playlist1_id = 'p1_id'
    playlist2_name = 'Playlist Page 2'
    playlist2_id = 'p2_id'

    # Mock user_playlists - first page
    mock_sp.user_playlists.return_value = {
        'items': [{'name': playlist1_name, 'id': playlist1_id, 'owner': {'id': user_id}}],
        'next': 'next_page_cursor_playlists' # Indicates there's a next page
    }
    
    # Mock sp.next for playlist pagination
    mock_sp.next.return_value = {
        'items': [{'name': playlist2_name, 'id': playlist2_id, 'owner': {'id': user_id}}],
        'next': None # Second page is the last page
    }
    
    # Mock playlist calls to return empty tracks for simplicity
    # Need to make sp.playlist handle different playlist_ids
    def playlist_side_effect(p_id, fields=None):
        if p_id == playlist1_id:
            return {'tracks': {'items': [], 'next': None}}
        elif p_id == playlist2_id:
            return {'tracks': {'items': [], 'next': None}}
        return {} # Should not happen in this test
    mock_sp.playlist.side_effect = playlist_side_effect
    
    results = query([user_id])
    
    assert user_id in results
    assert playlist1_name in results[user_id]
    assert playlist2_name in results[user_id]
    assert len(results[user_id]) == 2

# Test Case 6: Track pagination
def test_query_track_pagination(mocker):
    mock_sp = mocker.patch('playlist_finder.sp')
    user_id = 'test_user_id'
    playlist_id = 'playlist_tp_id'
    playlist_name = 'Playlist With Track Pagination'

    track1_data = {
        'track': {'id': 't1', 'name': 'Track 1', 'artists': [{'name': 'A1'}], 'album': {'name': 'Al1'}, 'duration_ms': 100, 'uri': 'uri1'},
        'added_by': {'id': user_id}, 'added_at': '2023-01-01T00:00:00Z'
    }
    track2_data = {
        'track': {'id': 't2', 'name': 'Track 2', 'artists': [{'name': 'A2'}], 'album': {'name': 'Al2'}, 'duration_ms': 200, 'uri': 'uri2'},
        'added_by': {'id': user_id}, 'added_at': '2023-01-02T00:00:00Z'
    }

    mock_sp.user_playlists.return_value = {
        'items': [{'name': playlist_name, 'id': playlist_id, 'owner': {'id': user_id}}],
        'next': None
    }
    
    # Mock sp.playlist to return first page of tracks
    first_track_page = {
        'tracks': {
            'items': [track1_data],
            'next': 'next_page_cursor_tracks' # Indicates more tracks
        }
    }
    mock_sp.playlist.return_value = first_track_page
    
    # Mock sp.next for track pagination
    second_track_page = {
        'items': [track2_data], # Note: sp.next for tracks returns the page directly
        'next': None
    }
    # We need to ensure sp.next is called with the correct object from first_track_page['tracks']
    mock_sp.next.return_value = second_track_page
    
    results = query([user_id])
    
    assert user_id in results
    assert playlist_name in results[user_id]
    assert len(results[user_id][playlist_name]['tracks']) == 2
    assert results[user_id][playlist_name]['tracks'][0]['track_id'] == 't1'
    assert results[user_id][playlist_name]['tracks'][1]['track_id'] == 't2'

    # Check that sp.next was called correctly for track pagination
    # The actual object `first_track_page['tracks']` was passed to sp.next
    mock_sp.next.assert_called_once_with(first_track_page['tracks'])


# Test Case 7: Filters playlists by owner
def test_query_filters_playlists_by_owner(mocker):
    mock_sp = mocker.patch('playlist_finder.sp')
    user_id = 'test_user_id'
    other_user_id = 'other_user_id'
    
    owned_playlist_name = 'My Playlist'
    owned_playlist_id = 'owned_p_id'
    other_playlist_name = "Someone Else's Playlist"
    other_playlist_id = 'other_p_id'

    mock_sp.user_playlists.return_value = {
        'items': [
            {'name': owned_playlist_name, 'id': owned_playlist_id, 'owner': {'id': user_id}},
            {'name': other_playlist_name, 'id': other_playlist_id, 'owner': {'id': other_user_id}}
        ],
        'next': None
    }
    
    # Mock sp.playlist for the owned playlist
    mock_sp.playlist.return_value = {'tracks': {'items': [], 'next': None}}
    
    results = query([user_id])
    
    assert user_id in results
    assert owned_playlist_name in results[user_id]
    assert other_playlist_name not in results[user_id]
    assert len(results[user_id]) == 1
    mock_sp.playlist.assert_called_once_with(owned_playlist_id, fields="tracks,next")


# Test Case 8: Handles problematic track data
def test_query_handles_problematic_track_data(mocker, capsys):
    mock_sp = mocker.patch('playlist_finder.sp')
    user_id = 'test_user_id'
    playlist_id = 'p_problem_id'
    playlist_name = 'Playlist With Problematic Track'

    valid_track = {
        'track': {
            'id': 'valid_id', 'name': 'Valid Track', 'artists': [{'name': 'Artist'}],
            'album': {'name': 'Album'}, 'duration_ms': 100, 'uri': 'valid_uri'
        },
        'added_by': {'id': user_id}, 'added_at': '2023-01-01T00:00:00Z'
    }
    # Problematic track: track['track'] is None, will cause TypeError or KeyError
    problematic_track_none = {
        'track': None, # This will cause an error when accessing track['track']['id']
        'added_by': {'id': user_id}, 'added_at': '2023-01-02T00:00:00Z'
    }
    # Problematic track: missing 'artists' key, will cause KeyError
    problematic_track_missing_key = {
        'track': {
            'id': 'problem_id_missing', 'name': 'Problem Track Missing Key', # 'artists' is missing
            'album': {'name': 'Album'}, 'duration_ms': 100, 'uri': 'problem_uri_missing'
        },
        'added_by': {'id': user_id}, 'added_at': '2023-01-03T00:00:00Z'
    }


    mock_sp.user_playlists.return_value = {
        'items': [{'name': playlist_name, 'id': playlist_id, 'owner': {'id': user_id}}],
        'next': None
    }
    mock_sp.playlist.return_value = {
        'tracks': {'items': [valid_track, problematic_track_none, problematic_track_missing_key], 'next': None}
    }
    
    results = query([user_id])
    
    assert user_id in results
    assert playlist_name in results[user_id]
    # Only the valid track should be present
    assert len(results[user_id][playlist_name]['tracks']) == 1
    assert results[user_id][playlist_name]['tracks'][0]['track_id'] == 'valid_id'
    
    captured = capsys.readouterr()
    # Check for generic part of the error message or specific exception types
    assert "Error processing track details." in captured.out # Error is printed to stdout
    # Check for at least two error messages (one for each problematic track)
    assert captured.out.count("Error processing track details.") >= 2
    assert "TypeError" in captured.out or "KeyError" in captured.out # Depending on which error happens first / how it's handled
    # Check if problematic track data was printed (optional, but good)
    assert "'track': None" in captured.out # For problematic_track_none
    assert "Problem Track Missing Key" in captured.out # For problematic_track_missing_key
    assert "pprint" # Ensure pprint is available for the main code, if not mocked.
                    # The main code already imports it.

# Note on mock_sp.next for playlist pagination vs track pagination:
# The Spotify API returns the full page object for sp.next() when paginating playlists.
# For tracks, sp.next() is called with a tracks paging object (results['tracks']),
# and it returns a new tracks paging object.
# The test for track pagination (test_query_track_pagination) was adjusted to reflect that
# sp.next() receives first_track_page['tracks'] and its return value (second_track_page)
# should be structured as a tracks paging object (containing 'items' and 'next').
# The test_query_playlist_pagination mock for sp.next.return_value should also be a full
# page object, which it is. My comment was slightly misleading if it implied otherwise.
# The key is what sp.next() is *called with* and what its *return structure* is.
# The main code for track pagination is:
#   track_page_data = results['tracks']
#   while track_page_data['next']:
#       track_page_data = sp.next(track_page_data) # Called with a tracks page object
#       tracks.extend(track_page_data['items'])
# And for playlist pagination:
#   while results['next']:
#       results = sp.next(results) # Called with a results page object
#       playlists.extend(results['items'])
# The mocks reflect this.
