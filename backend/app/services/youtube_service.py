import os
import requests
from typing import List, Dict, Any

# Note: os.getenv is called at request time so it reflects the current env
def get_learning_videos(concepts: List[str], max_total: int = 5) -> List[Dict[str, Any]]:
    """
    Fetch personalized learning recommendations using YouTube Data API v3.
    Falls back to YouTube search URL cards if the API key is not set or the call fails.
    """
    api_key = os.getenv("YOUTUBE_API_KEY", "").strip()

    if not concepts:
        concepts = ["Data Structures and Algorithms"]

    if not api_key:
        # Fallback: generate YouTube search URL cards without needing an API key
        return _fallback_search_links(concepts, max_total)

    recommendations: List[Dict[str, Any]] = []
    base_url = "https://www.googleapis.com/youtube/v3/search"

    # Limit to top 5 concepts to avoid excessive quota usage
    top_concepts: List[str] = []
    for c in concepts:
        top_concepts.append(c)
        if len(top_concepts) == 5:
            break
    concepts = top_concepts

    num_concepts = len(concepts) or 1
    videos_per_concept = max(1, max_total // num_concepts)
    remainder = max_total % num_concepts

    for i, concept in enumerate(concepts):
        limit = videos_per_concept + (1 if i < remainder else 0)
        if limit == 0:
            continue

        params = {
            "part": "snippet",
            "q": f"{concept} programming tutorial",
            "type": "video",
            "maxResults": limit,
            "key": api_key
        }

        try:
            response = requests.get(base_url, params=params, timeout=10)
            print(f"[YouTube] Concept={concept!r} status={response.status_code}")
            if response.status_code == 200:
                data = response.json()
                for item in data.get("items", []):
                    vid_id = item.get("id", {}).get("videoId")
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
            else:
                print(f"[YouTube] Error body: {response.text[:300]}")
        except Exception as e:
            print(f"[YouTube] Exception for {concept!r}: {e}")

    # If API gave nothing useful, fall back
    if not recommendations:
        return _fallback_search_links(concepts, max_total)

    final_videos: List[Dict[str, Any]] = []
    for vid in recommendations:
        final_videos.append(vid)
        if len(final_videos) == max_total:
            break

    return final_videos


def _fallback_search_links(concepts: List[str], max_total: int) -> List[Dict[str, Any]]:
    """
    When the YouTube API is unavailable, produce search-link cards that still
    let users navigate directly to relevant YouTube searches.
    """
    import urllib.parse

    results: List[Dict[str, Any]] = []
    for concept in concepts:
        query = urllib.parse.quote_plus(f"{concept} programming tutorial")
        results.append({
            "title": f"Search YouTube: {concept} Programming Tutorial",
            "channel": "YouTube Search",
            "video_id": "",
            "thumbnail": f"https://img.shields.io/badge/{urllib.parse.quote(concept)}-tutorial-red?style=for-the-badge&logo=youtube",
            "url": f"https://www.youtube.com/results?search_query={query}",
            "concept": concept
        })
        if len(results) == max_total:
            break

    return results
