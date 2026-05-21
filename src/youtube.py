"""YouTube research pipeline: handle → recent videos → transcripts."""

from __future__ import annotations

import re
import subprocess
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import feedparser
import requests
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound

UA = {"User-Agent": "Mozilla/5.0 (research; personal use)"}


@dataclass
class Video:
    video_id: str
    title: str
    published: str  # ISO timestamp from RSS
    url: str


def resolve_channel_id(handle_or_url: str) -> str:
    """Resolve a @handle or channel URL to a UC... channel_id.

    Uses the page's <link rel="canonical"> (authoritative for the channel itself),
    then falls back to "externalId" in the page data blob. We avoid the first
    "channelId":"UC..." match because that often points to a related/recommended
    channel, not the one the URL is for.
    """
    url = (
        handle_or_url
        if handle_or_url.startswith("http")
        else f"https://www.youtube.com/{handle_or_url.lstrip('/')}"
    )
    html = requests.get(url, headers=UA, timeout=15).text
    m = re.search(
        r'<link rel="canonical" href="https://www\.youtube\.com/channel/(UC[\w-]+)"', html
    ) or re.search(r'"externalId":"(UC[\w-]{20,})"', html)
    if not m:
        raise RuntimeError(f"could not resolve channel_id from {url}")
    return m.group(1)


def fetch_recent_videos(
    handle_or_url: str,
    n: int | None = 10,
    since: str | None = None,
) -> list[Video]:
    """Pull the channel RSS (≤15 recent) and return videos.

    If `since` (YYYY-MM-DD) is given, return all videos published on or after that date
    (n is ignored). Otherwise return the first n videos.
    """
    channel_id = resolve_channel_id(handle_or_url)
    feed = feedparser.parse(f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}")
    cutoff = datetime.strptime(since, "%Y-%m-%d").replace(tzinfo=timezone.utc) if since else None
    out: list[Video] = []
    for entry in feed.entries:
        published = entry.published  # ISO 8601 e.g. 2026-05-18T...Z
        if cutoff is not None:
            entry_dt = datetime.fromisoformat(published.replace("Z", "+00:00"))
            if entry_dt < cutoff:
                continue
        vid = entry.yt_videoid  # type: ignore[attr-defined]
        out.append(Video(video_id=vid, title=entry.title, published=published, url=entry.link))
        if cutoff is None and n is not None and len(out) >= n:
            break
    return out


def _parse_vtt(vtt_text: str) -> str:
    """Strip VTT timestamps, tags, and duplicate consecutive cue lines."""
    lines: list[str] = []
    last = None
    for raw in vtt_text.splitlines():
        s = raw.strip()
        if not s or s.startswith(("WEBVTT", "NOTE", "Kind:", "Language:")):
            continue
        if "-->" in s or re.fullmatch(r"\d+", s):
            continue
        s = re.sub(r"<[^>]+>", "", s)  # strip <c> tags
        s = re.sub(r"&nbsp;", " ", s).strip()
        if s and s != last:
            lines.append(s)
            last = s
    return " ".join(lines)


def fetch_transcript_via_ytdlp(
    video_id: str,
    cookies_file: str | None = None,
    cookies_browser: str | None = None,
    languages: tuple[str, ...] = ("en", "en-US"),
) -> str | None:
    """Fetch auto-generated subtitles via yt-dlp and parse to plain text.

    Pass `cookies_file` (a Netscape cookies.txt path) for parallel fetches —
    `cookies_browser` re-reads the OS keyring on every call and triggers a
    permission prompt per call on macOS.
    """
    with tempfile.TemporaryDirectory() as td:
        cmd = [
            "yt-dlp",
            "--skip-download",
            "--write-auto-sub",
            "--sub-format",
            "vtt",
            "--sub-langs",
            ",".join(languages),
            "--output",
            f"{td}/%(id)s.%(ext)s",
            f"https://www.youtube.com/watch?v={video_id}",
        ]
        if cookies_file:
            cmd.extend(["--cookies", cookies_file])
        elif cookies_browser:
            cmd.extend(["--cookies-from-browser", cookies_browser])
        try:
            subprocess.run(cmd, capture_output=True, timeout=60, check=False)
        except subprocess.TimeoutExpired:
            return None
        for vtt in Path(td).glob(f"{video_id}*.vtt"):
            return _parse_vtt(vtt.read_text())
    return None


def fetch_transcript(
    video_id: str,
    languages: tuple[str, ...] = ("en", "en-US"),
    cookies_file: str | None = None,
    cookies_browser: str | None = None,
) -> str | None:
    """Return plain-text transcript. Uses yt-dlp when cookies given, otherwise
    the anonymous transcript API (which gets IP-blocked easily)."""
    if cookies_file or cookies_browser:
        return fetch_transcript_via_ytdlp(
            video_id,
            cookies_file=cookies_file,
            cookies_browser=cookies_browser,
            languages=languages,
        )
    try:
        api = YouTubeTranscriptApi()
        fetched = api.fetch(video_id, languages=list(languages))
        return " ".join(snippet.text for snippet in fetched)
    except (TranscriptsDisabled, NoTranscriptFound):
        return None
    except Exception:
        return None


def fetch_transcripts_for(
    videos: list[Video],
    cookies_file: str | None = None,
    cookies_browser: str | None = None,
    max_workers: int = 2,
    delay: float = 1.0,
) -> list[tuple[Video, str | None]]:
    """Fetch transcripts for a list of videos with bounded concurrency.

    Defaults are deliberately gentle (max_workers=2, delay=1.0s between submissions)
    because aggressive parallel fetches reliably trigger YouTube's per-IP rate limit.
    """
    if not videos:
        return []
    results: dict[str, str | None] = {}
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures: dict = {}
        for i, v in enumerate(videos):
            if i > 0 and delay > 0:
                time.sleep(delay)
            fut = pool.submit(
                fetch_transcript,
                v.video_id,
                cookies_file=cookies_file,
                cookies_browser=cookies_browser,
            )
            futures[fut] = v.video_id
        for fut in as_completed(futures):
            results[futures[fut]] = fut.result()
    return [(v, results[v.video_id]) for v in videos]


def fetch_recent_with_transcripts(
    handle_or_url: str,
    n: int | None = 10,
    since: str | None = None,
    cookies_file: str | None = None,
    cookies_browser: str | None = None,
    max_workers: int = 2,
    delay: float = 1.0,
) -> list[tuple[Video, str | None]]:
    """Fetch recent videos and their transcripts. See fetch_recent_videos / fetch_transcripts_for."""
    videos = fetch_recent_videos(handle_or_url, n=n, since=since)
    return fetch_transcripts_for(
        videos,
        cookies_file=cookies_file,
        cookies_browser=cookies_browser,
        max_workers=max_workers,
        delay=delay,
    )


def dump_transcripts(items: list[tuple[Video, str | None]], outdir: str, label: str) -> list[str]:
    """Write each transcript to a wrapped .txt file under outdir, return paths."""
    import pathlib
    import textwrap

    root = pathlib.Path(outdir)
    root.mkdir(parents=True, exist_ok=True)
    paths: list[str] = []
    for i, (v, t) in enumerate(items):
        body = textwrap.fill(t or "", width=100)
        p = root / f"{label}_{i:02d}_{v.video_id}.txt"
        p.write_text(f"# {v.title}\n# {v.published}  {v.url}\n\n{body}\n")
        paths.append(str(p))
    return paths


if __name__ == "__main__":
    import argparse
    import json

    ap = argparse.ArgumentParser()
    ap.add_argument("handle", help="@handle or channel URL")
    ap.add_argument("--since", help="YYYY-MM-DD; pull all videos on/after this date")
    ap.add_argument("--n", type=int, default=10, help="if --since not given, pull last N videos")
    ap.add_argument("--dump", help="dir to write per-video transcript .txt files")
    ap.add_argument("--label", default="vid", help="filename prefix when dumping")
    ap.add_argument(
        "--cookies",
        dest="cookies_file",
        help="path to a Netscape cookies.txt (preferred for parallel fetches)",
    )
    ap.add_argument(
        "--cookies-from-browser",
        dest="cookies_browser",
        help="extract cookies fresh from browser each call (chrome/firefox/safari) — prompts repeatedly",
    )
    args = ap.parse_args()

    items = fetch_recent_with_transcripts(
        args.handle,
        n=args.n,
        since=args.since,
        cookies_file=args.cookies_file,
        cookies_browser=args.cookies_browser,
    )
    if args.dump:
        paths = dump_transcripts(items, args.dump, args.label)
    else:
        paths = [None] * len(items)
    for (v, t), p in zip(items, paths):
        print(
            json.dumps(
                {
                    "id": v.video_id,
                    "title": v.title,
                    "published": v.published,
                    "url": v.url,
                    "has_transcript": t is not None,
                    "chars": len(t) if t else 0,
                    "path": p,
                }
            )
        )
