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
