"""Bilibili 元数据获取"""

import time
from typing import List, Optional
from urllib.parse import urlencode

import requests

from config import (
    BILI_VIEW_API,
    BILI_PLAYER_WBI_API,
    BILI_PLAYER_V2_API,
    BILI_SERIES_API,
    BILI_FAVLIST_API,
    build_headers,
    REQUEST_TIMEOUT,
    MAX_RETRIES,
    RETRY_DELAY,
)
from models import VideoMeta, VideoPage


# 全局 cookie，由主程序设置
_global_cookie: str = ""


def set_cookie(cookie: str) -> None:
    """设置全局 Cookie，供后续 API 请求使用。"""
    global _global_cookie
    _global_cookie = cookie.strip() if cookie else ""


def _get_json(url: str, params: Optional[dict] = None) -> dict:
    """带重试的 GET 请求。"""
    last_error = None
    headers = build_headers(_global_cookie)
    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.get(
                url,
                params=params,
                headers=headers,
                timeout=REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            last_error = e
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))
    raise last_error or RuntimeError(f"请求失败: {url}")


def fetch_video_meta(bvid: str) -> VideoMeta:
    """获取视频元数据。"""
    payload = _get_json(BILI_VIEW_API, {"bvid": bvid})
    if payload.get("code") != 0:
        raise RuntimeError(payload.get("message", "无法获取视频信息"))

    data = payload.get("data", {})
    pubdate = int(data.get("pubdate") or 0)
    upload_date = ""
    if pubdate > 0:
        upload_date = time.strftime("%Y-%m-%d", time.localtime(pubdate))

    pages = []
    for item in data.get("pages") or []:
        pages.append(
            VideoPage(
                cid=str(item.get("cid") or ""),
                page=int(item.get("page") or 1),
                part=str(item.get("part") or "").strip(),
                duration=float(item.get("duration") or 0),
            )
        )

    return VideoMeta(
        bvid=bvid,
        aid=str(data.get("aid") or ""),
        cid=str(data.get("cid") or ""),
        title=str(data.get("title") or ""),
        author=str(data.get("owner", {}).get("name") or ""),
        description=str(data.get("desc") or ""),
        upload_date=upload_date,
        duration=float(data.get("duration") or 0),
        pages=pages,
    )


def fetch_subtitle_tracks(bvid: str, cid: str, aid: str) -> List[dict]:
    """获取视频可用字幕轨道列表。"""
    # 优先使用 wbi/v2 接口
    urls_to_try = []
    if aid:
        urls_to_try.append(
            (
                BILI_PLAYER_WBI_API,
                {"aid": aid, "cid": cid, "bvid": bvid},
            )
        )
    urls_to_try.append(
        (BILI_PLAYER_V2_API, {"bvid": bvid, "cid": cid, "aid": aid})
    )

    last_error = None
    for url, params in urls_to_try:
        try:
            payload = _get_json(url, params)
            if payload.get("code") != 0:
                # 可重试错误码
                code = payload.get("code")
                if code in (-509, -3) or (isinstance(code, int) and code < 0):
                    last_error = RuntimeError(payload.get("message", "API 错误"))
                    continue
                raise RuntimeError(payload.get("message", "无法获取字幕列表"))

            subtitles = payload.get("data", {}).get("subtitle", {}).get("subtitles", [])
            tracks = []
            for item in subtitles:
                url_str = item.get("subtitle_url") or ""
                if url_str.startswith("//"):
                    url_str = f"https:{url_str}"
                elif url_str and not url_str.startswith(("http://", "https://")):
                    url_str = f"https://{url_str.lstrip('/')}"

                lan = str(item.get("lan") or "").lower()
                tracks.append(
                    {
                        "id": str(item.get("id")) if item.get("id") is not None else "",
                        "lan": lan,
                        "lan_doc": item.get("lan_doc") or "",
                        "subtitle_url": url_str,
                        "is_ai": lan.startswith("ai-"),
                    }
                )
            return tracks
        except Exception as e:
            last_error = e
            continue

    raise last_error or RuntimeError("无法获取字幕列表")


def fetch_collection_videos(collection_type: str, params: dict) -> List[str]:
    """获取合集/收藏夹中的所有 BV 号。"""
    bvids = []

    if collection_type in ("series", "collection"):
        sid = params.get("sid")
        mid = params.get("mid", "")
        if not sid:
            return bvids

        pn = 1
        while True:
            payload = _get_json(
                BILI_SERIES_API,
                {
                    "mid": mid,
                    "series_id": sid,
                    "only_normal": "true",
                    "pn": pn,
                    "ps": 30,
                },
            )
            if payload.get("code") != 0:
                break

            archives = payload.get("data", {}).get("archives", [])
            if not archives:
                break

            for item in archives:
                bvid = item.get("bvid")
                if bvid:
                    bvids.append(bvid)

            if len(archives) < 30:
                break
            pn += 1
            time.sleep(0.5)

    elif collection_type == "favlist":
        mlid = params.get("mlid")
        if not mlid:
            return bvids

        pn = 1
        while True:
            payload = _get_json(
                BILI_FAVLIST_API,
                {
                    "media_id": mlid,
                    "pn": pn,
                    "ps": 20,
                    "platform": "web",
                },
            )
            if payload.get("code") != 0:
                break

            medias = payload.get("data", {}).get("medias", [])
            if not medias:
                break

            for item in medias:
                bvid = item.get("bvid") or item.get("upper", {}).get("bvid")
                if bvid:
                    bvids.append(bvid)

            if len(medias) < 20:
                break
            pn += 1
            time.sleep(0.5)

    elif collection_type == "watchlater":
        # 稍后再看需要登录 cookie，暂时不支持未登录获取
        raise NotImplementedError("稍后再看需要登录，请使用 bv 号列表或导出后粘贴链接")

    return bvids
