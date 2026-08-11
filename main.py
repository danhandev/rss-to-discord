"""RSS -> Discord 릴레이 (v2).

- stream 모드: 새 글이 나오면 바로 전송
- digest 모드: 새 글을 쌓아두었다가 주 1회 한 메시지로 묶어서 전송
- 피드가 제공하는 요약(summary/description)을 embed 본문에 함께 표시
"""

import html
import json
import os
import pathlib
import re
import sys
import time
from typing import Any

import feedparser
import requests
import yaml

ROOT = pathlib.Path(__file__).parent
STATE_PATH = ROOT / "state.json"

MAX_PER_RUN = 5           # stream 모드에서 피드당 한 번에 보낼 최대 개수
FIRST_RUN_SEND = 2        # 신규 피드 등록 시 최신 몇 건을 보낼지
KEEP_PER_FEED = 200       # state.json 비대화 방지
SUMMARY_LIMIT = 280       # embed 본문 길이 제한
DIGEST_MAX_LINES = 40     # 다이제스트 한 메시지 최대 줄 수

TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")


# ---------- state ----------

def load_state() -> dict[str, Any]:
    if STATE_PATH.exists():
        try:
            data = json.loads(STATE_PATH.read_text(encoding="utf-8") or "{}")
        except json.JSONDecodeError:
            print("! state.json 손상 — 초기화합니다", file=sys.stderr)
            data = {}
        data.setdefault("seen", {})
        data.setdefault("pending", {})
        return data
    return {"seen": {}, "pending": {}}


def save_state(state: dict[str, Any]) -> None:
    STATE_PATH.write_text(
        json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
    )


# ---------- 파싱 ----------

def entry_id(entry: Any) -> str:
    return entry.get("id") or entry.get("guid") or entry.get("link", "")


def extract_summary(entry: Any) -> str:
    """피드가 주는 요약에서 HTML 태그를 걷어내고 잘라낸다."""
    raw = ""
    if entry.get("summary"):
        raw = entry["summary"]
    elif entry.get("content"):
        raw = entry["content"][0].get("value", "")
    elif entry.get("description"):
        raw = entry["description"]

    text = WS_RE.sub(" ", html.unescape(TAG_RE.sub(" ", raw))).strip()
    if len(text) > SUMMARY_LIMIT:
        text = text[:SUMMARY_LIMIT].rsplit(" ", 1)[0] + "…"
    return text


def matches(entry: Any, include: list[str] | None) -> bool:
    if not include:
        return True
    title = entry.get("title", "")
    return any(k.lower() in title.lower() for k in include)


# ---------- 전송 ----------

def _post(webhook: str, payload: dict) -> bool:
    """전송 실패는 False만 반환한다. 예외로 죽으면 state가 저장되지 않는다."""
    try:
        resp = requests.post(webhook, json=payload, timeout=20)
        if resp.status_code == 429:
            time.sleep(float(resp.json().get("retry_after", 1)) + 0.5)
            resp = requests.post(webhook, json=payload, timeout=20)
        if resp.status_code >= 300:
            print(f"  ! 전송 실패 {resp.status_code}: {resp.text[:200]}", file=sys.stderr)
            return False
        return True
    except requests.RequestException as exc:
        print(f"  ! 네트워크 오류: {exc}", file=sys.stderr)
        return False


def send_item(webhook: str, source: str, item: dict) -> bool:
    return _post(webhook, {
        "embeds": [{
            "title": item["title"][:250],
            "url": item["link"],
            "description": item["summary"],
            "footer": {"text": source},
        }]
    })


def send_digest(webhook: str, channel: str, items: list[dict]) -> bool:
    """쌓인 항목을 출처별로 묶어 한 메시지로 보낸다."""
    by_source: dict[str, list[dict]] = {}
    for it in items:
        by_source.setdefault(it["source"], []).append(it)

    lines = [f"**주간 다이제스트 — {channel}** ({len(items)}건)", ""]
    for source, group in by_source.items():
        lines.append(f"__{source}__")
        for it in group:
            lines.append(f"· [{it['title'][:90]}]({it['link']})")
        lines.append("")
        if len(lines) > DIGEST_MAX_LINES:
            lines.append(f"…외 다수")
            break

    return _post(webhook, {"content": "\n".join(lines)[:1900]})


# ---------- 메인 ----------

def main() -> int:
    digest_run = os.environ.get("DIGEST", "").lower() in ("1", "true", "yes")
    config = yaml.safe_load((ROOT / "feeds.yml").read_text(encoding="utf-8"))
    state = load_state()
    seen_all: dict[str, list[str]] = state.setdefault("seen", {})
    pending_all: dict[str, list[dict]] = state.setdefault("pending", {})
    sent = 0

    for channel in config["channels"]:
        name = channel["name"]
        mode = channel.get("mode", "stream")
        webhook = os.environ.get(channel["webhook_env"], "").strip()
        if not webhook:
            print(f"[skip] {name}: {channel['webhook_env']} 미설정")
            continue

        for feed in channel["feeds"]:
            url = feed["url"]
            print(f"[{name}/{mode}] {feed['name']}")

            parsed = feedparser.parse(url)
            if parsed.bozo and not parsed.entries:
                print(f"  ! 파싱 실패: {parsed.get('bozo_exception')}", file=sys.stderr)
                continue

            seen = seen_all.setdefault(url, [])
            first_run = not seen

            fresh = [
                e for e in reversed(parsed.entries)
                if entry_id(e) not in seen and matches(e, feed.get("include"))
            ]

            if first_run and len(fresh) > FIRST_RUN_SEND:
                # 과거 글 폭탄 방지: 최신 몇 건만 남기고 나머지는 기록만
                for e in fresh[:-FIRST_RUN_SEND]:
                    seen.append(entry_id(e))
                fresh = fresh[-FIRST_RUN_SEND:]
                print(f"  신규 피드: 최신 {len(fresh)}건만 반영")

            # stream은 한 번에 쏟아지지 않게 제한, digest는 전부 쌓아둔다
            batch = fresh[-MAX_PER_RUN:] if mode == "stream" else fresh
            items = [{
                "source": feed["name"],
                "title": e.get("title", "(제목 없음)"),
                "link": e.get("link", ""),
                "summary": extract_summary(e),
            } for e in batch]

            for entry, item in zip(batch, items):
                if mode == "digest":
                    pending_all.setdefault(name, []).append(item)
                    seen.append(entry_id(entry))
                elif send_item(webhook, feed["name"], item):
                    seen.append(entry_id(entry))
                    sent += 1
                    time.sleep(1)

            seen_all[url] = seen[-KEEP_PER_FEED:]

        # 다이제스트 발송 시점
        if mode == "digest" and digest_run:
            queued = pending_all.get(name, [])
            if queued and send_digest(webhook, name, queued):
                sent += len(queued)
                pending_all[name] = []
            elif not queued:
                print(f"  다이제스트: 보낼 항목 없음")

    save_state(state)
    print(f"완료: {sent}건 전송 (digest_run={digest_run})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
