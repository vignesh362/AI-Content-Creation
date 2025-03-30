import os
import numpy as np
import isodate
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv
import requests 
from video_utils import generate_dialogue_script

# Load API keys
load_dotenv()
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Setup clients
youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
genai.configure(api_key=GEMINI_API_KEY)
# gemini_model = genai.GenerativeModel("gemini-pro")
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

MIN_TRANSCRIPT_LENGTH = 100
MIN_VIDEO_DURATION_SECONDS = 4 * 60  # 2 minutes

def get_transcript_text(video_id):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
        cleaned = [seg['text'] for seg in transcript if seg['text'].strip().lower() not in ['[music]']]
        return ' '.join(cleaned)

    except (TranscriptsDisabled, NoTranscriptFound):
        return ""
    except Exception as e:
        print(f"[ERROR] Transcript error for {video_id}: {e}")
        return ""

# def generate_summary(text: str) -> str:
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
        
        headers = {
            "Content-Type": "application/json"
        }

        prompt = f"Summarize this transcript in 3-5 sentences:\n{text[:10000]}"
        
        data = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ]
        }

        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        
        result = response.json()
        return result["candidates"][0]["content"]["parts"][0]["text"]

    except Exception as e:
        print(f"[ERROR] Gemini HTTP error: {e}")
        return "Summary generation failed."

def parse_duration(duration_str):
    try:
        return isodate.parse_duration(duration_str).total_seconds()
    except Exception as e:
        print(f"[ERROR] parse_duration error: {e}")
        return 0

def get_top_videos_for_keyword(query, max_results=10):
    all_items = []
    next_page_token = None
    while len(all_items) < max_results:
        request = youtube.search().list(
            part='snippet',
            type='video',
            q=query,
            order='viewCount',
            maxResults=min(50, max_results - len(all_items)),
            pageToken=next_page_token
        )
        response = request.execute()
        all_items.extend(response['items'])
        next_page_token = response.get('nextPageToken')
        if not next_page_token:
            break
    print(f"[DEBUG] Fetched {len(all_items)} search results for query '{query}'")
    return all_items

def get_video_details(video_ids):
    stats = []
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i + 50]
        response = youtube.videos().list(
            part='snippet,statistics,contentDetails',
            id=','.join(batch)
        ).execute()
        stats.extend(response['items'])
    print(f"[DEBUG] Retrieved details for {len(stats)} videos")
    return stats

def get_top_channels_for_topic(topic: str, top_n: int = 3):
    print(f"[INFO] Getting top videos for topic: {topic}")
    search_results = get_top_videos_for_keyword(topic, max_results=50)
    video_ids = [item['id']['videoId'] for item in search_results if 'videoId' in item['id']]
    print(f"[DEBUG] Extracted {len(video_ids)} video IDs")
    detailed_videos = get_video_details(video_ids)
    topic_embedding = embedding_model.encode(topic)

    channels = {}
    accepted_videos = 0

    for item in detailed_videos:
        if 'snippet' not in item or 'statistics' not in item or 'contentDetails' not in item:
            print(f"[SKIP] Missing snippet/statistics/contentDetails in item {item.get('id', 'unknown')}")
            continue

        snippet = item['snippet']
        stats = item['statistics']
        content_details = item['contentDetails']
        duration_seconds = parse_duration(content_details.get('duration', 'PT0S'))

        if duration_seconds < MIN_VIDEO_DURATION_SECONDS:
            print(f"[SKIP] Video {item['id']} skipped due to short duration: {duration_seconds:.1f}s")
            continue

        video_id = item['id']
        title = snippet.get('title', '')
        description = snippet.get('description', '')
        views = int(stats.get('viewCount', 0))
        channel_id = snippet.get('channelId')
        channel_title = snippet.get('channelTitle', '')
        transcript = get_transcript_text(video_id)

        if len(transcript.split()) < MIN_TRANSCRIPT_LENGTH:
            print(f"[SKIP] Video {video_id} has short/empty transcript: {len(transcript.split())} words")
            continue

        combined_text = f"{title} {description} {transcript}"
        embedding = embedding_model.encode(combined_text)
        relevance = float(np.dot(embedding, topic_embedding) / (np.linalg.norm(embedding) * np.linalg.norm(topic_embedding)))

        summary = generate_dialogue_script(transcript)
        source = "youtube" if transcript else "ai"

        video_info = {
            "video_id": video_id,
            "title": title,
            "description": description,
            "views": views,
            "relevance": relevance,
            "summary": summary,
            "source": source,
            "transcript": transcript
        }
        print(f"[ACCEPTED] Video: {title} | Views: {views} | Relevance: {relevance:.3f}")
        accepted_videos += 1

        if channel_id not in channels:
            channels[channel_id] = {
                "channel_title": channel_title,
                "videos": []
            }
        channels[channel_id]["videos"].append(video_info)

    print(f"[SUMMARY] Total accepted videos: {accepted_videos}")

    # Rank channels
    scored = []
    for cid, info in channels.items():
        vids = info["videos"]
        if not vids:
            continue
        avg_rel = np.mean([v["relevance"] for v in vids])
        total_views = sum([v["views"] for v in vids])
        score = 0.6 * avg_rel + 0.4 * (total_views / 1e6)
        scored.append({
            "channel_id": cid,
            "channel_title": info["channel_title"],
            "total_views": total_views,
            "avg_relevance": avg_rel,
            "score": score,
            "videos": sorted(vids, key=lambda v: v["views"], reverse=True)[:top_n]
        })
    print(f"[DEBUG] {len(scored)} channels scored")
    print(f"[DEBUG] Scored channels: {scored}")

    return sorted(scored, key=lambda x: x["score"], reverse=True)[:top_n]
