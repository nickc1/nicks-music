#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "requests",
#     "python-dotenv",
# ]
# ///
"""Save every artist you currently follow on Spotify to a JSON file.

Setup:
1. Create an app at https://developer.spotify.com/dashboard
2. Add a Redirect URI of http://127.0.0.1:8888/callback to the app settings
3. Copy scripts/.env.example to scripts/.env and fill in the client id/secret
4. Run: uv run scripts/spotify_following.py

The first run opens a browser for you to authorize the app, then stores a
refresh token in scripts/.env so future runs don't need re-authorization.
Results are written to scripts/spotify_following.json.
"""

import json
import os
import sys
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import requests
from dotenv import load_dotenv, set_key

ENV_PATH = Path(__file__).parent / ".env"
OUTPUT_PATH = Path(__file__).parent / "spotify_following.json"
load_dotenv(ENV_PATH)

CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = os.environ.get("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8888/callback")
SCOPE = "user-follow-read"

AUTH_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"
API_URL = "https://api.spotify.com/v1/me/following"


def require_client_credentials():
    if not CLIENT_ID or not CLIENT_SECRET:
        sys.exit(
            "Missing SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET.\n"
            "Copy scripts/.env.example to scripts/.env and fill them in "
            "(create an app at https://developer.spotify.com/dashboard)."
        )


class _CallbackHandler(BaseHTTPRequestHandler):
    auth_code = None

    def do_GET(self):
        params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        _CallbackHandler.auth_code = params.get("code", [None])[0]
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"<html><body>Authorized \xe2\x80\x94 you can close this tab.</body></html>")

    def log_message(self, *args):
        pass


def authorize() -> str:
    parsed = urllib.parse.urlparse(REDIRECT_URI)
    server = HTTPServer((parsed.hostname, parsed.port), _CallbackHandler)

    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPE,
    }
    url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"
    print(f"Opening browser for Spotify authorization:\n{url}", flush=True)
    webbrowser.open(url)

    while _CallbackHandler.auth_code is None:
        server.handle_request()

    resp = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": _CallbackHandler.auth_code,
            "redirect_uri": REDIRECT_URI,
        },
        auth=(CLIENT_ID, CLIENT_SECRET),
    )
    resp.raise_for_status()
    tokens = resp.json()

    set_key(str(ENV_PATH), "SPOTIFY_REFRESH_TOKEN", tokens["refresh_token"])
    return tokens["access_token"]


def refresh_access_token(refresh_token: str) -> str:
    resp = requests.post(
        TOKEN_URL,
        data={"grant_type": "refresh_token", "refresh_token": refresh_token},
        auth=(CLIENT_ID, CLIENT_SECRET),
    )
    resp.raise_for_status()
    tokens = resp.json()
    if "refresh_token" in tokens:
        set_key(str(ENV_PATH), "SPOTIFY_REFRESH_TOKEN", tokens["refresh_token"])
    return tokens["access_token"]


def get_access_token() -> str:
    refresh_token = os.environ.get("SPOTIFY_REFRESH_TOKEN")
    if refresh_token:
        try:
            return refresh_access_token(refresh_token)
        except requests.HTTPError:
            print("Stored refresh token is no longer valid, re-authorizing...")
    return authorize()


def fetch_followed_artists(access_token: str) -> list[dict]:
    headers = {"Authorization": f"Bearer {access_token}"}
    artists = []
    after = None
    while True:
        params = {"type": "artist", "limit": 50}
        if after:
            params["after"] = after
        resp = requests.get(API_URL, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json()["artists"]
        artists.extend(data["items"])
        after = data["cursors"].get("after")
        if not after:
            break
    return artists


def to_record(artist: dict) -> dict:
    images = artist.get("images") or []
    return {
        "id": artist["id"],
        "name": artist["name"],
        "genres": artist.get("genres", []),
        "followers": artist.get("followers", {}).get("total", 0),
        "popularity": artist.get("popularity", 0),
        "spotify_url": artist.get("external_urls", {}).get("spotify"),
        "image": images[0]["url"] if images else None,
    }


def main():
    require_client_credentials()
    ENV_PATH.touch(exist_ok=True)

    access_token = get_access_token()
    artists = fetch_followed_artists(access_token)
    records = sorted((to_record(a) for a in artists), key=lambda a: a["name"].lower())

    OUTPUT_PATH.write_text(json.dumps(records, indent=2, ensure_ascii=False) + "\n")
    print(f"Saved {len(records)} followed artist(s) to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
