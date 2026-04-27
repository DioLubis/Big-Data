from typing import List, Dict, Optional
from googleapiclient.discovery import build


def fetch_comments(
    api_key: str,
    video_id: str,
    max_comments: Optional[int] = None,
) -> List[Dict[str, str]]:
    youtube = build("youtube", "v3", developerKey=api_key)

    comments = []
    next_page_token = None

    while True:
        request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=100,
            textFormat="plainText",
            pageToken=next_page_token,
            order="relevance",
        )
        response = request.execute()

        for item in response.get("items", []):
            top_comment = item["snippet"]["topLevelComment"]["snippet"]
            comments.append(
                {
                    "video_id": video_id,
                    "author": top_comment.get("authorDisplayName", ""),
                    "text": top_comment.get("textDisplay", ""),
                    "like_count": top_comment.get("likeCount", 0),
                    "published_at": top_comment.get("publishedAt", ""),
                }
            )
            if max_comments is not None and len(comments) >= max_comments:
                break

        if max_comments is not None and len(comments) >= max_comments:
            break

        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break

    return comments


def fetch_comments_multi_video(
    api_key: str,
    video_ids: List[str],
    max_comments_per_video: Optional[int] = None,
) -> List[Dict[str, str]]:
    all_comments: List[Dict[str, str]] = []
    for vid in [v.strip() for v in video_ids if v.strip()]:
        all_comments.extend(fetch_comments(api_key, vid, max_comments=max_comments_per_video))
    return all_comments
