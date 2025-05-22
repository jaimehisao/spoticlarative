# spoticlarative
[![Python CI & Test](https://github.com/jaimehisao/playlists/actions/workflows/ci.yml/badge.svg)](https://github.com/jaimehisao/playlists/actions/workflows/ci.yml)

Spoticlarative is a Python application designed to track changes in your Spotify playlists over time. It achieves this by fetching playlist data, storing it in JSON files, and using a Git repository to version these files. This allows you to see how your playlists evolve, what tracks are added or removed, and by whom (if applicable for collaborative playlists).

The primary benefit is creating a historical archive of your playlists, offering insights into your musical journey.

## Setup and Installation

### Prerequisites
- Python 3.7+ recommended.
- Git installed on your system.
- A Spotify account.

### Steps

1.  **Clone this application repository:**
    ```bash
    git clone https://github.com/jaimehisao/spoticlarative.git
    cd spoticlarative
    ```

2.  **Prepare a separate Git repository for playlist data:**
    This is where Spoticlarative will store your playlist JSON files. Create a new repository (e.g., on GitHub, GitLab) if you don't have one already. Copy its HTTPS or SSH URL. This will be your `REMOTE` URL.

3.  **Install dependencies:**
    The required Python packages are listed in `requirements.txt`.
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up environment variables:**
    Environment variables are used to store sensitive information like API keys and your Git remote URL.
    - Copy the example environment file:
      ```bash
      cp .env.example .env
      ```
    - Edit the `.env` file with your actual values:
        - `SPOTIPY_CLIENT_ID`: Your Spotify application Client ID.
        - `SPOTIPY_CLIENT_SECRET`: Your Spotify application Client Secret.
        - `SPOTIPY_REDIRECT_URI`: The Redirect URI you configured in your Spotify application (e.g., `http://localhost:8888/callback`). *Ensure this exact URI is added to your application settings on the Spotify Developer Dashboard.*
        - `REMOTE`: The Git URL of the repository you prepared in step 2 (e.g., `https://github.com/your_username/my_spotify_playlists_archive.git`).

    > **Note:** You can find `SPOTIPY_CLIENT_ID`, `SPOTIPY_CLIENT_SECRET`, and set up `SPOTIPY_REDIRECT_URI` by creating an application at the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/applications).

## How it Works

The script executes the following workflow:

1.  **Clones Data Repository**: It clones the Git repository specified by the `REMOTE` environment variable into a temporary local directory (`tmp/`).
2.  **Fetches Playlists**: Using the Spotify API (via the `spotipy` library), it fetches playlist data for the users defined in `main.py`.
3.  **Compares Data**: The fetched playlist data is compared against the existing JSON files (if any) in the cloned `tmp/` directory.
4.  **Updates and Commits**:
    - If changes are detected for a playlist (new tracks, removed tracks, reordered tracks), the corresponding JSON file is updated.
    - If a playlist is new, a new JSON file is created.
    - Changes for each user are committed to the Git repository with a user-specific commit message.
5.  **Pushes Changes**: If any commits were made, the script pushes all changes to the `REMOTE` repository.

## Configuration

User configuration, specifically defining which Spotify users' playlists to track, is done directly within the `main.py` script:

-   **`USERS`**: This is a Python dictionary that maps Spotify user IDs (or usernames as recognized by the Spotify API for some endpoints) to the desired directory names within the Git repository. This also influences commit messages.
    *Example:* `{'spotify_user_id1': 'friendly_name_for_user1', '1234567890': 'another_user_name'}`

-   **`USERS_TO_STORE`**: This is a Python list containing the keys (Spotify user IDs/usernames) from the `USERS` dictionary whose playlists the script should actively process.
    *Example:* `['spotify_user_id1', '1234567890']`

## Running the Script

To run the script manually:
```bash
python main.py
```
The script is designed to be run periodically (e.g., using a cron job or a scheduled task) to keep the playlist archive updated with the latest changes. Each run will fetch the current state of playlists and commit any detected differences.

## Testing

To ensure the application functions correctly and to catch regressions, unit tests are provided.

1.  **Install development dependencies** (which includes testing tools like `pytest`):
    ```bash
    pip install -r requirements.txt
    ```

2.  **Run the tests** using `pytest` from the project root directory:
    ```bash
    pytest
    ```

## Continuous Integration

This project uses GitHub Actions to automatically run tests on every push and pull request to the `main` branch. This helps maintain code quality and ensures that changes integrate smoothly. (See the status badge at the top of this README for the current build status).

## Project Structure

A brief overview of the project's directory structure:

-   `main.py`: The main executable script that orchestrates the playlist fetching, comparison, and Git update processes.
-   `playlist_finder.py`: A module responsible for all interactions with the Spotify API, including authentication and data retrieval for playlists and tracks.
-   `requirements.txt`: Lists the Python dependencies required for the project.
-   `.env.example`: An example file showing the environment variables needed. You should copy this to `.env` and fill in your actual credentials.
-   `tests/`: Contains all unit tests for the project. Pytest is used as the testing framework.
-   `.github/workflows/ci.yml`: Defines the GitHub Actions workflow for continuous integration (automated testing).
-   `README.md`: This file – providing documentation for the project.

Playlists retrieved by the script are stored in a separate Git repository that you configure (via the `REMOTE` environment variable). Inside that repository, they are typically organized by user, with each playlist as a JSON file.
