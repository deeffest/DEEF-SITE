import os

import requests
from flask import Flask, redirect
from flask_caching import Cache

app = Flask(__name__)
cache = Cache(
    app,
    config={
        "CACHE_TYPE": "filesystem",
        "CACHE_DIR": "/tmp/flask_cache",
        "CACHE_DEFAULT_TIMEOUT": 1800,
    },
)

APPS = {
    "ytmdplayer": "deeffest/YouTube-Music-Desktop-Player",
}

ASSETS = {
    "latest_deb": "Linux-amd64.deb",
    "latest_rpm": "Linux-x86_64.rpm",
    "latest_setup_exe": "Win32-Setup.exe",
    "latest_tar_xz": "Linux.tar.xz",
    "latest_rar": "Win32.rar",
    "qt5_latest_tar_xz": "Linux-Qt5.tar.xz",
    "qt5_latest_rar": "Win32-Qt5.rar",
}


@cache.memoize()
def get_asset_url(repo: str, filename: str) -> str | None:
    token = os.getenv("GITHUB_TOKEN")
    headers = {"Authorization": f"token {token}"} if token else {}
    try:
        r = requests.get(
            f"https://api.github.com/repos/{repo}/releases/latest",
            headers=headers,
            timeout=10,
        )
        r.raise_for_status()
        for asset in r.json().get("assets", []):
            if asset["name"].endswith(filename):
                return asset["browser_download_url"]
        app.logger.warning("No asset matching %r in %s", filename, repo)
    except Exception:
        app.logger.exception("GitHub API request failed for %s", repo)
    return None


@app.route("/")
def home():
    return redirect("https://github.com/deeffest")


@app.route("/<app>/<asset>")
def get_app(app, asset):
    repo = APPS.get(app)
    filename = ASSETS.get(asset)
    if not repo or not filename:
        return "Not found", 404
    url = get_asset_url(repo, filename)
    return redirect(url) if url else ("File not found", 404)


if __name__ == "__main__":
    app.run(debug=False, port=1428)
