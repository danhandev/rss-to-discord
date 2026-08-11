# mode: stream  = 새 글이 나오면 바로 전송
# mode: digest  = 쌓아뒀다가 주 1회 한 메시지로 전송
#
# 주의: 같은 URL을 두 채널에 넣지 마세요. 중복 판정 키가 URL이라
#       먼저 처리된 채널에서만 전송됩니다.

channels:

  # ── 매일 볼 것. 요약이 붙어 있어 제목만으로 판단 가능 ──
  - name: "daily"
    webhook_env: DISCORD_WEBHOOK_DAILY
    mode: stream
    feeds:
      - name: "GeekNews"
        url: "https://news.hada.io/rss/news"
      - name: "Hacker News 100+"
        url: "https://hnrss.org/frontpage?points=100"
      - name: "Spring Blog"
        url: "https://spring.io/blog.atom"
        include: ["This Week in Spring"]   # 릴리스 노트 제외
      # TLDR 뉴스레터: RSS가 없습니다.
      # kill-the-newsletter.com에서 주소를 발급받아 그 주소로 구독한 뒤,
      # 발급된 피드 URL을 아래에 넣으세요.
      # - name: "TLDR"
      #   url: "https://kill-the-newsletter.com/feeds/발급받은키.xml"

  # ── 주 1회 몰아서 볼 것 (기업 기술블로그) ──
  - name: "weekly-tech"
    webhook_env: DISCORD_WEBHOOK_WEEKLY
    mode: digest
    feeds:
      - name: "토스테크"
        url: "https://toss.tech/rss.xml"
      - name: "우아한형제들"
        url: "https://techblog.woowahan.com/feed"
      - name: "카카오"
        url: "https://tech.kakao.com/feed/"
      - name: "카카오페이"
        url: "https://tech.kakaopay.com/rss.xml"
      - name: "뱅크샐러드"
        url: "https://blog.banksalad.com/rss.xml"
      - name: "NAVER D2"
        url: "https://d2.naver.com/d2.atom"
      - name: "LINE"
        url: "https://techblog.lycorp.co.jp/ko/feed/index.xml"
      - name: "당근"
        url: "https://medium.com/feed/daangn"
      - name: "쿠팡"
        url: "https://medium.com/feed/coupang-engineering"
      - name: "컬리"
        url: "https://helloworld.kurly.com/feed.xml"
      - name: "데브시스터즈"
        url: "https://tech.devsisters.com/rss.xml"
      - name: "쏘카"
        url: "https://tech.socarcorp.kr/feed"
      - name: "하이퍼커넥트"
        url: "https://hyperconnect.github.io/feed.xml"
      - name: "요즘IT"
        url: "https://yozm.wishket.com/magazine/feed/"

  # ── 금융 규제/정책. 실시간일 이유가 없으니 주 1회 ──
  # 아래 주소는 각 기관 RSS 안내 페이지에서 직접 복사해서 채우세요.
  #   금융위원회  https://www.fsc.go.kr/ut060101  (보도자료 항목)
  #   한국은행    bok.or.kr 하단 RSS 안내
  #   금융보안원  fsec.or.kr 자료실 (RSS 미제공 시 생략)
  - name: "weekly-finance"
    webhook_env: DISCORD_WEBHOOK_FINANCE
    mode: digest
    feeds: []
      # - name: "금융위 보도자료"
      #   url: "여기에 붙여넣기"
      # - name: "한국은행 보도자료"
      #   url: "여기에 붙여넣기"
