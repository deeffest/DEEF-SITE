import os
import requests
from flask import Flask, render_template, redirect
from flask_caching import Cache

app = Flask(__name__)
cache = Cache(app, config={"CACHE_TYPE": "simple", "CACHE_DEFAULT_TIMEOUT": 1800})

apps = [
    {
        "title": "Youtube Music Desktop Player",
        "desc": "Turns the YT Music site into a desktop application.",
        "platforms": "Windows · Linux",
        "github": "https://github.com/deeffest/Youtube-Music-Desktop-Player",
        "repo": "deeffest/Youtube-Music-Desktop-Player",
    },
]

YTMD_ASSETS = {
    "latest_deb": ".deb",
    "latest_rpm": ".rpm",
    "latest_setup_exe": "Win32-Setup.exe",
    "latest_tar_xz": ".tar.xz",
    "latest_rar": ".rar",
}


def get_latest_release(repo: str) -> str:
    cache_key = f"version_{repo}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    url = f"https://api.github.com/repos/{repo}/releases/latest"
    headers = {}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"
    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        version = r.json().get("tag_name", "unknown")
        cache.set(cache_key, version)
        return version
    except Exception:
        return "unknown"


def get_latest_asset_url(repo: str, asset_match: str) -> str:
    cache_key = f"asset_{repo}_{asset_match}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    url = f"https://api.github.com/repos/{repo}/releases/latest"
    headers = {}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"
    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        assets = r.json().get("assets", [])
        for asset in assets:
            if asset_match in asset["name"]:
                asset_url = asset["browser_download_url"]
                cache.set(cache_key, asset_url)
                return asset_url
    except Exception:
        return None
    return None


@app.route("/")
@cache.cached()
def home():
    apps_with_versions = []
    for app_info in apps:
        version = get_latest_release(app_info["repo"])
        app_copy = app_info.copy()
        app_copy["version"] = version
        apps_with_versions.append(app_copy)
    return render_template("home.html", apps=apps_with_versions)


@app.route("/ytmdplayer/<asset>")
@cache.cached()
def ytmdplayer(asset):
    if asset not in YTMD_ASSETS:
        return "Asset not found", 404

    repo = "deeffest/Youtube-Music-Desktop-Player"
    url = get_latest_asset_url(repo, YTMD_ASSETS[asset])
    if url:
        return redirect(url)
    return "File not found", 404


if __name__ == "__main__":
    app.run(debug=False, port=1428)
