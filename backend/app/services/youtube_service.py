import os
import requests
from typing import List, Dict, Any

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")

def get_learning_videos(concepts: List[str]) -> List[Dict[str, Any]]:
    """
    Fetch personalized learning recommendations using YouTube Data API v3.
    """
    if not YOUTUBE_API_KEY or not concepts:
        return []

    recommendations = []
    base_url = "https://www.googleapis.com/youtube/v3/search"

    # Search up to 5 videos for each concept to give a good variety
    for concept in concepts:
        params = {
            "part": "snippet",
            "q": f"{concept} programming tutorial",
            "type": "video",
            "maxResults": 3,  # Adjusted to 3 per concept so we cover 2-3 lowest concepts evenly
            "key": YOUTUBE_API_KEY
        }
        
        try:
            response = requests.get(base_url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                for item in data.get("items", []):
                    vid_id = item["id"].get("videoId")
                    snippet = item.get("snippet", {})
                    if vid_id:
                        recommendations.append({
                            "title": snippet.get("title", ""),
                            "channel": snippet.get("channelTitle", ""),
                            "video_id": vid_id,
                            "thumbnail": f"https://img.youtube.com/vi/{vid_id}/0.jpg",
                            "url": f"https://youtube.com/watch?v={vid_id}",
                            "concept": concept
                        })
        except Exception as e:
            print(f"Error fetching YouTube recommendations for {concept}: {e}")

    # Return up to 6 unique recommendations natively matching responsive grids
    return recommendations[:6]
