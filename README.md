# RSS → Discord

feeds.yml에 등록한 RSS를 주기적으로 읽어, 새 글만 Discord 채널로 보낸다.
GitHub Actions에서 돌기 때문에 서버가 필요 없다.

## 세팅

1. Discord에서 채널 3개 생성: `#korea-tech`, `#java-spring`, `#global`
2. 각 채널 → 채널 편집 → 연동 → 웹후크 → 새 웹후크 → URL 복사
3. 이 폴더를 GitHub 저장소로 push (**private 권장** — 웹훅 URL은 Secrets에만 둔다)
4. 저장소 Settings → Secrets and variables → Actions에 등록
   - `DISCORD_WEBHOOK_KOREA`
   - `DISCORD_WEBHOOK_JAVA`
   - `DISCORD_WEBHOOK_GLOBAL`
5. Actions 탭 → RSS to Discord → Run workflow 로 첫 실행

## 동작

- 최초 실행: 과거 글을 쏟아내지 않도록 id만 기록하고 전송하지 않는다
- 이후: 새 글만 전송, 피드당 한 번에 최대 5건
- 처리한 글 id는 `state.json`에 남고 Actions가 자동 커밋한다
- `include`를 주면 제목에 해당 키워드가 있는 글만 보낸다
  (예: Spring Blog에서 "This Week in Spring"만)

## 피드 추가

`feeds.yml`의 해당 채널 아래에 `name`과 `url`을 추가하고 push하면 끝.
RSS 주소를 모르면 블로그 주소 뒤에 `/feed`, `/rss.xml`, `/feed.xml`,
`/atom.xml`을 붙여 보거나 페이지 소스에서 `application/rss+xml`을 찾는다.

## 로컬 테스트

    pip install -r requirements.txt
    DISCORD_WEBHOOK_KOREA="웹훅URL" python main.py

# RSS → Discord v2

v1에서 달라진 점
- 피드가 제공하는 요약을 Discord embed 본문에 함께 표시
- 채널별 mode: stream(즉시) / digest(주 1회 묶음)
- 전송 실패가 예외로 번져 state를 날리던 문제 수정
- push 충돌 시 rebase 후 재시도

## 마이그레이션 (v1을 이미 돌리고 있다면)

1. main.py, feeds.yml, .github/workflows/rss.yml 교체
2. state.json 삭제 (구조가 {"seen":..., "pending":...}로 바뀜)
3. Discord 채널을 daily / weekly-tech / weekly-finance 로 정리하고
   웹훅 3개를 Secrets에 등록
   - DISCORD_WEBHOOK_DAILY
   - DISCORD_WEBHOOK_WEEKLY
   - DISCORD_WEBHOOK_FINANCE
4. push 후 Actions에서 Run workflow

state.json을 지우면 각 피드의 최신 2건이 들어옵니다(FIRST_RUN_SEND).
digest 채널은 그 2건이 pending에 쌓였다가 월요일에 한 번에 옵니다.
바로 확인하려면 Run workflow에서 digest 체크박스를 켜세요.

## 튜닝

main.py 상단 상수
- MAX_PER_RUN: stream 채널에서 한 번에 보낼 최대 개수
- SUMMARY_LIMIT: embed 본문 길이 (기본 280자)
- DIGEST_MAX_LINES: 다이제스트 한 메시지 최대 줄 수

