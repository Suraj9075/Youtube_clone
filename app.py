# app.py
import os
import time
import random
import traceback
from typing import Dict, Any, List

from flask import Flask, request, jsonify, render_template
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# YouTube API Key
API_KEY = os.environ.get("YOUTUBE_API_KEY")
if not API_KEY:
    raise RuntimeError("Set YOUTUBE_API_KEY in environment")

# Config
DEFAULT_MAX_RESULTS = 50
MAX_ALLOWED_RESULTS = 1000
SEARCH_PAGE_SIZE = 50
SLEEP_BETWEEN_PAGES = 0.15


# -------------------- Helpers --------------------

def create_youtube_service():
    return build("youtube", "v3", developerKey=API_KEY)


def build_query(interests: List[str]) -> str:
    niche_filters = {
        "ai": 'neural networks -"machine learning"',
        "gardening": 'heirloom -"home depot"',
        "retro_gaming": '"CRT" -"nintendo"',
    }
    return " OR ".join(f"({niche_filters.get(i, i)})" for i in interests)


def iso_duration_to_readable(dur: str) -> str:
    try:
        dur = dur.replace("PT", "")
        h = m = s = 0
        if "H" in dur:
            h, dur = dur.split("H")
            h = int(h)
        if "M" in dur:
            m, dur = dur.split("M")
            m = int(m)
        if "S" in dur:
            s = int(dur.replace("S", ""))
        return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"
    except Exception:
        return dur


# -------------------- Routes --------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/digest")
def get_digest():
    raw = request.args.get("interests")
    if not raw:
        return jsonify({"error": "Provide interests like ?interests=ai,gardening"}), 400

    interests = [i.strip() for i in raw.split(",") if i.strip()]
    if not interests:
        return jsonify({"error": "Invalid interests"}), 400

    try:
        max_results = int(request.args.get("maxResults", DEFAULT_MAX_RESULTS))
    except ValueError:
        max_results = DEFAULT_MAX_RESULTS

    max_results = min(max(max_results, 1), MAX_ALLOWED_RESULTS)
    query = build_query(interests)

    try:
        youtube = create_youtube_service()

        video_ids = []
        items = []
        next_token = None
        remaining = max_results

        while remaining > 0:
            response = youtube.search().list(
                q=query,
                part="id,snippet",
                type="video",
                maxResults=min(SEARCH_PAGE_SIZE, remaining),
                order="viewCount",
                pageToken=next_token
            ).execute()

            for item in response.get("items", []):
                vid = item["id"].get("videoId")
                if vid:
                    video_ids.append(vid)
                    items.append(item)
                    remaining -= 1

            next_token = response.get("nextPageToken")
            if not next_token:
                break

            time.sleep(SLEEP_BETWEEN_PAGES)

        videos = []
        if video_ids:
            for i in range(0, len(video_ids), 50):
                stats = youtube.videos().list(
                    id=",".join(video_ids[i:i + 50]),
                    part="statistics,contentDetails"
                ).execute()

                stats_map = {v["id"]: v for v in stats.get("items", [])}

                for item in items[i:i + 50]:
                    vid = item["id"]["videoId"]
                    snip = item["snippet"]
                    stat = stats_map.get(vid, {})

                    duration = stat.get("contentDetails", {}).get("duration")
                    videos.append({
                        "id": vid,
                        "title": snip["title"],
                        "channel": snip["channelTitle"],
                        "thumbnail": snip["thumbnails"]["default"]["url"],
                        "url": f"https://youtu.be/{vid}",
                        "view_count": stat.get("statistics", {}).get("viewCount"),
                        "duration": iso_duration_to_readable(duration) if duration else None
                    })

        return jsonify({
            "requested": max_results,
            "returned": len(videos),
            "videos": videos
        })

    except HttpError as e:
        return jsonify({"error": "YouTube API error", "details": str(e)}), 502
    except Exception as e:
        return jsonify({"error": "Server error", "details": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
