"""RSS -> Discord 릴레이.

feeds.yml에 정의된 피드를 순회하며, 아직 보내지 않은 글만
채널별 Discord 웹훅으로 전송한다. 처리한 글의 id는 state.json에 남긴다.
"""

import json
import os
import pathlib
import sys
import time
from typing import Any

import feedparser
import requests
import yaml

ROOT = pathlib.Path(__file__).parent
STATE_PATH = ROOT / "state.json"
MAX_PER_RUN = 5          # 피드 하나당 한 번에 보낼 최대 개수 (첫 실행 폭탄 방지)
KEEP_PER_FEED = 200      # state.json이 무한히 커지지 않도록 피드별 보관 개수


def load_state() -> dict[str, list[str]]:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    return {}


def save_state(state: dict[str, list[str]]) -> None:
    STATE_PATH.write_text(
        json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def entry_id(entry: Any) -> str:
    """피드마다 id/guid/link 중 있는 걸 쓴다."""
    return entry.get("id") or entry.get("guid") or entry.get("link", "")


def matches(entry: Any, include: list[str] | None) -> bool:
    if not include:
        return True
    title = entry.get("title", "")
    return any(keyword.lower() in title.lower() for keyword in include)


def post_to_discord(webhook: str, source: str, entry: Any) -> bool:
    payload = {
        "embeds": [
            {
                "title": entry.get("title", "(제목 없음)")[:250],
                "url": entry.get("link", ""),
                "description": "",
                "footer": {"text": source},
            }
        ]
    }
    resp = requests.post(webhook, json=payload, timeout=15)

    # Discord 웹훅 레이트리밋 대응
    if resp.status_code == 429:
        retry_after = resp.json().get("retry_after", 1)
        time.sleep(float(retry_after) + 0.5)
        resp = requests.post(webhook, json=payload, timeout=15)

    if resp.status_code >= 300:
        print(f"  ! 전송 실패 {resp.status_code}: {resp.text[:200]}", file=sys.stderr)
        return False
    return True


def main() -> int:
    config = yaml.safe_load((ROOT / "feeds.yml").read_text(encoding="utf-8"))
    state = load_state()
    sent_total = 0

    for channel in config["channels"]:
        webhook = os.environ.get(channel["webhook_env"], "").strip()
        if not webhook:
            print(f"[skip] {channel['name']}: {channel['webhook_env']} 미설정")
            continue

        for feed in channel["feeds"]:
            url, name = feed["url"], feed["name"]
            print(f"[{channel['name']}] {name}")

            parsed = feedparser.parse(url)
            if parsed.bozo and not parsed.entries:
                print(f"  ! 파싱 실패: {parsed.get('bozo_exception')}", file=sys.stderr)
                continue

            seen = state.setdefault(url, [])
            first_run = not seen

            # 피드는 최신순이므로 뒤집어서 오래된 것부터 보낸다
            new_entries = [
                e for e in reversed(parsed.entries)
                if entry_id(e) not in seen and matches(e, feed.get("include"))
            ]

            if first_run:
                # 최초 실행에서는 과거 글을 전부 쏘지 않고 id만 기록
                seen.extend(entry_id(e) for e in new_entries)
                print(f"  최초 실행: {len(new_entries)}건 기록만 하고 전송 생략")
                new_entries = []

            for entry in new_entries[-MAX_PER_RUN:]:
                if post_to_discord(webhook, name, entry):
                    seen.append(entry_id(entry))
                    sent_total += 1
                    time.sleep(1)  # 웹훅 초당 제한 여유

            state[url] = seen[-KEEP_PER_FEED:]

    save_state(state)
    print(f"완료: {sent_total}건 전송")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
