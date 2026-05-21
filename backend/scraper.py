import time
import requests
import csv
from urllib.parse import urlparse, parse_qs

def extract_video_id(youtube_url):
    parsed = urlparse(youtube_url)
    if parsed.hostname in ("youtu.be", "www.youtu.be"):
        return parsed.path.lstrip("/")
    if parsed.hostname in ("www.youtube.com", "youtube.com", "m.youtube.com"):
        qs = parse_qs(parsed.query)
        if "v" in qs:
            return qs["v"][0]
        path_parts = parsed.path.split("/")
        if "shorts" in path_parts:
            return path_parts[-1]
    raise ValueError("could not extract video id from url: " + youtube_url)

def get_video_title(api_key, video_id):
    url = "https://www.googleapis.com/youtube/v3/videos"
    params = {"part": "snippet", "id": video_id, "key": api_key}
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    data = resp.json()
    title = data["items"][0]["snippet"]["title"]
    safe_title = "".join(c for c in title if c.isalnum() or c in (" ", "-", "_")).rstrip()
    return safe_title or "youtube_comments"

def exponential_backoff_request(url, params, max_retries=6, backoff_base=1.5):
    for attempt in range(max_retries):
        resp = requests.get(url, params=params, timeout=30)
        if resp.status_code == 200:
            return resp
        if resp.status_code in (403, 429, 500, 503):
            wait = (backoff_base ** attempt) + (attempt * 0.5)
            time.sleep(wait)
            continue
        resp.raise_for_status()
    raise RuntimeError(f"max retries reached for url {url} (last status {resp.status_code})")

def fetch_all_comment_threads(api_key, video_id):
    endpoint = "https://www.googleapis.com/youtube/v3/commentThreads"
    params = {
        "part": "snippet",
        "videoId": video_id,
        "key": api_key,
        "maxResults": 100,
        "textFormat": "plainText",
        "order": "time"
    }

    comments = []
    next_token = None
    page = 0

    while True:
        if next_token:
            params["pageToken"] = next_token
        else:
            params.pop("pageToken", None)

        response = exponential_backoff_request(endpoint, params)
        data = response.json()
        items = data.get("items", [])
        page += 1
        comments.extend(items)

        next_token = data.get("nextPageToken")
        if not next_token:
            break

        time.sleep(0.1)
    return comments

def flatten_comment_thread(thread_item):
    s = thread_item["snippet"]
    top = s["topLevelComment"]["snippet"]
    return {
        "text": top.get("textDisplay"),
        "published_at": top.get("publishedAt"),
        "like_count": top.get("likeCount"),
        "reply_count": s.get("totalReplyCount", 0),
    }

def scrape_comments(api_key, video_url):
    video_id = extract_video_id(video_url)
    title = get_video_title(api_key, video_id)
    raw_comments = fetch_all_comment_threads(api_key, video_id)
    flat_comments = [flatten_comment_thread(c) for c in raw_comments]
    return title, flat_comments
