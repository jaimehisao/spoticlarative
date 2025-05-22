import pytest
from unittest.mock import patch, mock_open, MagicMock, call as mock_call # Import call
import json
import main # To run the script's main logic (main.run_main_logic)
from pathlib import Path # To help with mocking Path objects

# Sample data for tests
USER_ID_A = "jaimehisao" # Matches a key in main.USERS
REAL_USER_NAME_A = main.USERS[USER_ID_A] # "jaimehisao"
PLAYLIST_NAME_A = "My Test Playlist A"
PLAYLIST_FILENAME_A = "My Test Playlist A"
FULL_PLAYLIST_PATH_A = f"tmp/{REAL_USER_NAME_A}/{PLAYLIST_FILENAME_A}.json"

USER_ID_B = "marijojos99" # Another user from main.USERS
REAL_USER_NAME_B = main.USERS[USER_ID_B] # "marijojos99"
PLAYLIST_NAME_B = "My Test Playlist B"
PLAYLIST_FILENAME_B = "My Test Playlist B"
FULL_PLAYLIST_PATH_B = f"tmp/{REAL_USER_NAME_B}/{PLAYLIST_FILENAME_B}.json"

SAMPLE_PLAYLIST_DATA_A = {
    "id": "playlistA123",
    "tracks": [{"track_id": "trackA1", "track_name": "Song A1"}]
}
MODIFIED_PLAYLIST_DATA_A = {
    "id": "playlistA123",
    "tracks": [{"track_id": "trackA1", "track_name": "Song A1 v2"}]
}
SAMPLE_PLAYLIST_DATA_B = {
    "id": "playlistB456",
    "tracks": [{"track_id": "trackB1", "track_name": "Song B1"}]
}

PLAYLIST_NAME_SLASHED = "My/Playlist/With/Slashes"
PLAYLIST_NAME_SANITIZED = "My-Playlist-With-Slashes"
FULL_PLAYLIST_PATH_SANITIZED = f"tmp/{REAL_USER_NAME_A}/{PLAYLIST_NAME_SANITIZED}.json"


@pytest.fixture(autouse=True)
def mock_env_and_git(mocker):
    mocker.patch('main.load_dotenv') # Prevent .env loading
    mocker.patch('os.getenv', return_value='mock_remote_url')

    mock_repo_instance = MagicMock(spec=main.git.Repo)
    mock_index_instance = MagicMock(spec=main.git.Index)
    mock_remote_instance = MagicMock(spec=main.git.Remote)
    mock_config_writer_instance = MagicMock()

    mock_repo_instance.index = mock_index_instance
    mock_repo_instance.remote.return_value = mock_remote_instance
    
    # Mock the config_writer context manager
    # config_writer() returns a context manager, __enter__ is the actual object
    mock_repo_instance.config_writer.return_value.__enter__.return_value = mock_config_writer_instance
    
    mocker.patch('git.Repo.clone_from', return_value=mock_repo_instance)
    mocker.patch('pathlib.Path.mkdir')
    
    # Return the config writer mock to allow tests to access it directly if needed,
    # though accessing via main.repo.config_writer... is also possible.
    return mock_config_writer_instance


# Test Case 1: No changes to playlists
def test_main_no_changes(mocker):
    mocker.patch('main.query', return_value={
        USER_ID_A: {PLAYLIST_NAME_A: SAMPLE_PLAYLIST_DATA_A}
    })
    mocker.patch('builtins.open', mock_open(read_data=json.dumps(SAMPLE_PLAYLIST_DATA_A)))
    
    main.run_main_logic()
    
    main.repo.index.commit.assert_not_called()
    main.repo.remote.assert_called_once_with(name="origin")
    main.repo.remote().push.assert_not_called()

# Test Case 2: New playlist added
def test_main_new_playlist_added(mocker):
    mocker.patch('main.query', return_value={
        USER_ID_A: {PLAYLIST_NAME_A: SAMPLE_PLAYLIST_DATA_A}
    })
    
    mock_file = mock_open()
    mock_file.side_effect = [FileNotFoundError, mock_file.return_value]
    mocker.patch('builtins.open', mock_file)
    
    mock_json_dump = mocker.patch('json.dump')
    
    main.run_main_logic()

    main.pathlib.Path(f"tmp/{REAL_USER_NAME_A}").mkdir.assert_called_with(parents=True, exist_ok=True)
    assert mock_file.call_count == 2
    mock_file.assert_any_call(FULL_PLAYLIST_PATH_A, "r")
    mock_file.assert_any_call(FULL_PLAYLIST_PATH_A, "w")
    mock_json_dump.assert_called_once_with(SAMPLE_PLAYLIST_DATA_A, mock_file.return_value, indent=4)
    main.repo.index.add.assert_called_once_with([FULL_PLAYLIST_PATH_A])
    main.repo.index.commit.assert_called_once_with(f"Updating playlists for {REAL_USER_NAME_A}")
    main.repo.remote().push.assert_called_once()

# Test Case 3: Existing playlist modified
def test_main_existing_playlist_modified(mocker):
    mocker.patch('main.query', return_value={
        USER_ID_A: {PLAYLIST_NAME_A: MODIFIED_PLAYLIST_DATA_A}
    })
    
    mock_file = mock_open(read_data=json.dumps(SAMPLE_PLAYLIST_DATA_A))
    mocker.patch('builtins.open', mock_file)
    
    mock_json_dump = mocker.patch('json.dump')
    
    main.run_main_logic()
    
    assert mock_file.call_count == 2
    mock_file.assert_any_call(FULL_PLAYLIST_PATH_A, "r")
    mock_file.assert_any_call(FULL_PLAYLIST_PATH_A, "w")
    mock_json_dump.assert_called_once_with(MODIFIED_PLAYLIST_DATA_A, mock_file.return_value, indent=4)
    main.repo.index.add.assert_called_once_with([FULL_PLAYLIST_PATH_A])
    main.repo.index.commit.assert_called_once_with(f"Updating playlists for {REAL_USER_NAME_A}")
    main.repo.remote().push.assert_called_once()

# Test Case 4: Multiple users, mixed changes
def test_main_multiple_users_mixed_changes(mocker):
    mocker.patch('main.query', return_value={
        USER_ID_A: {PLAYLIST_NAME_A: MODIFIED_PLAYLIST_DATA_A}, # User A has changes
        USER_ID_B: {PLAYLIST_NAME_B: SAMPLE_PLAYLIST_DATA_B}    # User B no changes
    })

    # Mock open: User A's file exists and is different. User B's file exists and is identical.
    def open_side_effect(filepath, mode='r'):
        if filepath == FULL_PLAYLIST_PATH_A:
            if mode == 'r':
                return mock_open(read_data=json.dumps(SAMPLE_PLAYLIST_DATA_A)).return_value
            return mock_open().return_value # For write
        elif filepath == FULL_PLAYLIST_PATH_B:
            if mode == 'r': # User B, no change
                return mock_open(read_data=json.dumps(SAMPLE_PLAYLIST_DATA_B)).return_value
            # Write should not happen for User B
        raise FileNotFoundError(f"Unexpected file access: {filepath}")

    mocked_open = mocker.patch('builtins.open', side_effect=open_side_effect)
    mock_json_dump = mocker.patch('json.dump')

    main.run_main_logic()

    # Check mkdir calls
    main.pathlib.Path(f"tmp/{REAL_USER_NAME_A}").mkdir.assert_called_with(parents=True, exist_ok=True)
    main.pathlib.Path(f"tmp/{REAL_USER_NAME_B}").mkdir.assert_called_with(parents=True, exist_ok=True)
    
    # Check file operations for User A (changes)
    mocked_open.assert_any_call(FULL_PLAYLIST_PATH_A, 'r')
    mocked_open.assert_any_call(FULL_PLAYLIST_PATH_A, 'w')
    mock_json_dump.assert_any_call(MODIFIED_PLAYLIST_DATA_A, mocker.ANY, indent=4) # ANY for file handle

    # Check file operations for User B (no changes)
    mocked_open.assert_any_call(FULL_PLAYLIST_PATH_B, 'r')
    # Ensure no write call for User B's original file
    write_calls_for_B = [
        c for c in mocked_open.call_args_list 
        if c[0][0] == FULL_PLAYLIST_PATH_B and c[0][1] == 'w'
    ]
    assert len(write_calls_for_B) == 0
    
    # Check commits: User A committed, User B not.
    main.repo.index.add.assert_called_once_with([FULL_PLAYLIST_PATH_A]) # Only User A's change
    main.repo.index.commit.assert_called_once_with(f"Updating playlists for {REAL_USER_NAME_A}")
    
    # Overall push should happen
    main.repo.remote().push.assert_called_once()

# Test Case 5: Multiple users, all with changes
def test_main_multiple_users_all_with_changes(mocker):
    mocker.patch('main.query', return_value={
        USER_ID_A: {PLAYLIST_NAME_A: MODIFIED_PLAYLIST_DATA_A}, # User A has changes
        USER_ID_B: {PLAYLIST_NAME_B: MODIFIED_PLAYLIST_DATA_A}  # User B also has changes (using A's modified data for simplicity)
    })

    def open_side_effect(filepath, mode='r'):
        if filepath == FULL_PLAYLIST_PATH_A: # User A
            if mode == 'r': return mock_open(read_data=json.dumps(SAMPLE_PLAYLIST_DATA_A)).return_value
            return mock_open().return_value # For write
        elif filepath == FULL_PLAYLIST_PATH_B: # User B
            if mode == 'r': return mock_open(read_data=json.dumps(SAMPLE_PLAYLIST_DATA_B)).return_value
            return mock_open().return_value # For write
        raise FileNotFoundError(f"Unexpected file access: {filepath}")

    mocked_open = mocker.patch('builtins.open', side_effect=open_side_effect)
    mock_json_dump = mocker.patch('json.dump')

    main.run_main_logic()

    # Check adds
    add_calls = [
        mock_call([FULL_PLAYLIST_PATH_A]),
        mock_call([FULL_PLAYLIST_PATH_B])
    ]
    main.repo.index.add.assert_has_calls(add_calls, any_order=True)
    assert main.repo.index.add.call_count == 2

    # Check commits
    commit_calls = [
        mock_call(f"Updating playlists for {REAL_USER_NAME_A}"),
        mock_call(f"Updating playlists for {REAL_USER_NAME_B}")
    ]
    main.repo.index.commit.assert_has_calls(commit_calls, any_order=True)
    assert main.repo.index.commit.call_count == 2
    
    main.repo.remote().push.assert_called_once()

# Test Case 6: Playlist name sanitization
def test_main_playlist_name_sanitization(mocker):
    mocker.patch('main.query', return_value={
        USER_ID_A: {PLAYLIST_NAME_SLASHED: SAMPLE_PLAYLIST_DATA_A}
    })
    
    mock_file = mock_open()
    # Simulate file not found for the sanitized name, then allow write
    mock_file.side_effect = [FileNotFoundError, mock_file.return_value]
    mocker.patch('builtins.open', mock_file)
    
    mock_json_dump = mocker.patch('json.dump')

    main.run_main_logic()

    main.pathlib.Path(f"tmp/{REAL_USER_NAME_A}").mkdir.assert_called_with(parents=True, exist_ok=True)
    
    # Check open calls with sanitized path
    mock_file.assert_any_call(FULL_PLAYLIST_PATH_SANITIZED, "r")
    mock_file.assert_any_call(FULL_PLAYLIST_PATH_SANITIZED, "w")
    
    mock_json_dump.assert_called_once_with(SAMPLE_PLAYLIST_DATA_A, mock_file.return_value, indent=4)
    main.repo.index.add.assert_called_once_with([FULL_PLAYLIST_PATH_SANITIZED])
    main.repo.index.commit.assert_called_once_with(f"Updating playlists for {REAL_USER_NAME_A}")
    main.repo.remote().push.assert_called_once()

# Test Case 7: Git user config
def test_main_git_user_config(mocker, mock_env_and_git): # mock_env_and_git is autouse, but can be passed to access its return
    # mock_env_and_git fixture already sets up the mock_config_writer_instance
    # We can access it via the fixture's return value or via main.repo
    mock_config_writer_instance = mock_env_and_git 
    
    # No playlist changes needed for this test, query can return empty
    mocker.patch('main.query', return_value={})
    
    main.run_main_logic()

    # The mock_config_writer_instance is what __enter__ returns
    # from mock_repo_instance.config_writer.return_value in the fixture
    
    expected_calls = [
        mock_call("user", "email", "operations@hisao.org"),
        mock_call("user", "name", "Playlist-Bot-Prod")
    ]
    # Accessing via the fixture return value directly
    mock_config_writer_instance.set_value.assert_has_calls(expected_calls, any_order=True)
    assert mock_config_writer_instance.set_value.call_count == 2

    # Alternative access via main.repo (if fixture didn't return it)
    # config_writer_context_mgr = main.repo.config_writer()
    # actual_config_writer_obj = config_writer_context_mgr.__enter__()
    # actual_config_writer_obj.set_value.assert_has_calls(expected_calls, any_order=True)


# Final considerations for main.repo:
# The fixture mock_env_and_git patches 'git.Repo.clone_from'.
# main.run_main_logic() calls `repo = git.Repo.clone_from(...)`.
# So, `main.repo` (the global in main.py) will be `mock_repo_instance` from the fixture.
# Assertions like `main.repo.index.commit...` correctly use this mocked instance.
