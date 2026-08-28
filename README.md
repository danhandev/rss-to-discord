# RSS → Discord

`feeds.yml`에 등록한 RSS를 주기적으로 읽어 신규 업로드된 글만 Discord로 보냅니다. GitHub Actions를 활용해 서버가 필요하지 않습니다.

<br>

## 1. 만든 이유

IT 트렌드를 따라가고 인사이트를 얻기 위해 기술 블로그와 공식 사이트를 주기적으로 열람하고 있습니다. 사이트마다 직접 링크를 눌러 들어가야 했고, 안 읽은 글이 어디서부터인지 확인하는 일이 반복되어 수집을 자동화하기로 했습니다.

팀 프로젝트에서 이미 Discord를 사용하고 있기 때문에 저에게 접근성이 가장 좋은 Discord에 글이 모이도록 연결했습니다.

개인용 도구인 만큼 인프라 없이 최대한 간단하게 두고 싶었습니다. GitHub Actions 위에서 동작하도록 만들고, 상태는 DB 없이 저장소의 `state.json` 한 파일로만 관리하도록 했습니다.

<br>

## 2. 구독 중인 피드

실제로 연결해 둔 목록입니다. 해당 글들을 어떤 주기로 읽고 싶은지를 기준으로 채널을 나눴습니다.

### daily — 그날 보지 않으면 의미가 줄어드는 것

| 출처 | 비고 |
|---|---|
| GeekNews | 국내 개발자 커뮤니티에서 그날 논의되는 주제 |
| Hacker News | 100점 이상만 필터링해 상위 글만 수신 |
| Spring Blog | `This Week in Spring`만 필터링, 릴리스 노트는 제외 |

### weekly-tech — 기업 기술블로그, 주말에 몰아서

토스테크, 우아한형제들, 카카오, 카카오페이, 뱅크샐러드, NAVER D2, LINE, 당근, 쿠팡, 컬리, 데브시스터즈, 쏘카, 하이퍼커넥트, 요즘IT

트래픽과 데이터 규모가 큰 서비스가 어떤 문제를 어떻게 풀었는지 보려고 모았습니다. 업로드는 결제 및 정산을 다루는 토스테크, 카카오페이, 뱅크샐러드의 비중이 높습니다.

### weekly-finance — 금융 인프라와 정책

| 출처 | 다루는 것 |
|---|---|
| 금융위원회 보도자료 | 금융 규제·제도 변경 |
| 한국은행 지급결제보고서 | 지급결제 제도 현황 |
| 한국은행 지급결제 동향자료 | 결제 수단·금액 통계 |
| 한국은행 금융정보화 추진현황 | 금융권 IT 인프라 현황 |
| 한국은행 한은금융망 운영 및 구축 | 거액결제시스템(BOK-Wire+) 운영 |

백엔드 기술만으로는 보이지 않는 부분이라 따로 채널을 뒀습니다. 계정계와 지급결제처럼 은행 시스템이 실제로 어떤 제약 위에서 돌아가는지를 규제와 정책 쪽에서 함께 따라가려는 목적입니다. 실시간으로 볼 이유가 없어 주 1회로 묶었습니다.

<br>

## 3. 동작 방식

읽는 주기에 따라 피드를 분리했습니다. discord 채널 기준으로 **stream**(바로 전송)과 **digest**(주 1회 묶음) 중 하나를 고를 수 있습니다.

### 전송 모드 선택

| 모드 | 전송 시점 | 형태 | 쓰는 곳 |
|---|---|---|---|
| `stream` | 새 글 발견 즉시 (2시간마다 확인) | 글 1건 = embed 1개, 요약 포함 | 그때그때 보고 싶은 뉴스 |
| `digest` | 월요일 09:00 KST | 한 주치를 출처별로 묶은 메시지 1개 | 기업 기술블로그, 정책 자료 |

`stream`은 한 번에 쏟아지지 않도록 피드당 최대 5건(`MAX_PER_RUN`)까지만 보냅니다.
`digest`는 개수 제한 없이 쌓아두었다가 발송 시점에 한꺼번에 내보냅니다.

### 최초 실행 시 주의할 점

새 피드를 추가할 때 모든 글이 "안 읽은 글"로 간주됩니다. 방대한 양의 콘텐츠가 한번에 들어오는 일을 방지하기 위해 처음 보는 피드는 **최신 2건**(`FIRST_RUN_SEND`)만 전송하고,
나머지는 보낸 것으로 기록을 남깁니다.

### 중복 판정 원리

보낸 글의 id(`id` → `guid` → `link` 순으로 선택)를 `state.json`에 남기고, Actions가 실행 후 자동으로 커밋하여 다음 실행이 같은 글을 다시 보내지 않습니다.

```jsonc
{
  "seen":    { "<피드 URL>": ["<글 id>", ...] },   // 피드별 최근 200건
  "pending": { "weekly-tech": [ { "source": ..., "title": ..., "link": ..., "summary": ... } ] }
}
```

`pending`은 digest 채널이 발송 전까지 대기하는 필드입니다.

<br>

## 4. 세팅 방법

1. Discord에서 채널 3개를 만듭니다 — `daily`, `weekly-tech`, `weekly-finance`
2. 각 채널 → 채널 편집 → 연동 → 웹후크 → 새 웹후크 → **URL 복사**
3. 저장소 Settings → Secrets and variables → Actions → New repository secret 으로 3개 등록

   | Secret 이름 | 대응 채널 |
   |---|---|
   | `DISCORD_WEBHOOK_DAILY` | `daily` |
   | `DISCORD_WEBHOOK_WEEKLY` | `weekly-tech` |
   | `DISCORD_WEBHOOK_FINANCE` | `weekly-finance` |

4. Actions 탭 → **RSS to Discord** → Run workflow 로 첫 실행

Secret이 등록되지 않은 채널은 오류 없이 건너뜁니다(`[skip] ...: ... 미설정` 로그). 쓰고 싶은 채널만 등록하셔도 됩니다.

> **웹훅 URL은 절대 커밋하지 마세요.** URL 하나만 있으면 누구나 그 채널에 글을 쓸 수 있습니다.
> 실수로 커밋했다면 Discord 채널 설정에서 해당 웹훅을 삭제하고 새로 발급하세요.

<br>

## 5. 피드 추가

`feeds.yml`의 채널 아래에 `name`과 `url`을 추가하고 push해주세요. 

```yaml
channels:
  - name: "daily"
    webhook_env: DISCORD_WEBHOOK_DAILY
    mode: stream
    feeds:
      - name: "Spring Blog"
        url: "https://spring.io/blog.atom"
        include: ["This Week in Spring"]   # 제목에 이 키워드가 있는 글만
```

`include`를 주면 제목에 키워드(대소문자 무시)가 들어간 글만 보냅니다. 위 예시는 Spring Blog에서 릴리스 노트를 걸러내고 주간 요약만 받습니다.

RSS 주소를 모를 경우 블로그 주소 뒤에 `/feed`, `/rss.xml`, `/feed.xml`, `/atom.xml`을 붙여 보거나, 페이지 소스에서 `application/rss+xml`을 찾아보시길 추천드립니다!

<br>

## 6. 파일 구조

```
main.py                    피드 수집 → 필터 → 전송 → state 갱신
feeds.yml                  채널·피드 목록 (여기만 고치면 됩니다)
state.json                 보낸 글 id와 digest 대기열 — Actions가 자동 커밋
.github/workflows/rss.yml  2시간마다 stream, 월요일 digest
```

`main.py` 상단 상수로 동작을 조절할 수 있습니다.

| 상수 | 기본값 | 뜻 |
|---|---|---|
| `MAX_PER_RUN` | 5 | stream 모드에서 피드당 1회 최대 전송 수 |
| `FIRST_RUN_SEND` | 2 | 새 피드 등록 시 보낼 최신 글 수 |
| `KEEP_PER_FEED` | 200 | 피드별로 기억할 글 id 수 |
| `SUMMARY_LIMIT` | 280 | embed 본문에 넣을 요약 길이 |
| `DIGEST_MAX_LINES` | 40 | 다이제스트 한 메시지 최대 줄 수 |

<br>

## 7. License

MIT
