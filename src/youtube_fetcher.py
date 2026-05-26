from typing import Any, Dict, List, Optional
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


def fetch_comments(
    api_key: str,
    video_id: str,
    max_comments: Optional[int] = None,
) -> List[Dict[str, Any]]:
    youtube = build("youtube", "v3", developerKey=api_key)

    comments = []
    next_page_token = None

    while True:
        response = None
        for attempt in range(5):
            try:
                request = youtube.commentThreads().list(
                    part="id,snippet,replies",
                    videoId=video_id,
                    maxResults=100,
                    textFormat="plainText",
                    pageToken=next_page_token,
                    order="relevance",
                )
                response = request.execute(num_retries=3)
                break
            except (HttpError, TimeoutError, OSError):
                if attempt == 4:
                    return comments

        if response is None:
            break

        for item in response.get("items", []):
            top_comment_obj = item.get("snippet", {}).get("topLevelComment", {})
            top_comment = top_comment_obj.get("snippet", {})
            comments.append(
                {
                    "video_id": video_id,
                    "comment_id": top_comment_obj.get("id", ""),
                    "parent_comment_id": "",
                    "is_reply": False,
                    "kind": top_comment_obj.get("kind", ""),
                    "etag": top_comment_obj.get("etag", ""),
                    "channel_id": top_comment.get("channelId", ""),
                    "author": top_comment.get("authorDisplayName", ""),
                    "author_channel_id": top_comment.get("authorChannelId", {}).get("value", ""),
                    "author_channel_url": top_comment.get("authorChannelUrl", ""),
                    "author_profile_image_url": top_comment.get("authorProfileImageUrl", ""),
                    "text": top_comment.get("textDisplay", ""),
                    "text_original": top_comment.get("textOriginal", ""),
                    "like_count": top_comment.get("likeCount", 0),
                    "viewer_rating": top_comment.get("viewerRating", ""),
                    "can_rate": top_comment.get("canRate", None),
                    "published_at": top_comment.get("publishedAt", ""),
                    "updated_at": top_comment.get("updatedAt", ""),
                    "total_reply_count": item.get("snippet", {}).get("totalReplyCount", 0),
                    "raw_thread": item,
                    "raw_comment": top_comment_obj,
                    "raw_snippet": top_comment,
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
) -> List[Dict[str, Any]]:
    all_comments: List[Dict[str, Any]] = []
    for vid in [v.strip() for v in video_ids if v.strip()]:
        all_comments.extend(fetch_comments(api_key, vid, max_comments=max_comments_per_video))
    return all_comments
