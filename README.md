# 데일리 외신 영어 — AI 없이 돌아가는 로컬 버전

> **웹 버전**(컴퓨터를 켜 두지 않아도 매일 갱신, 휴대폰에서도 접속)은 [WEB_GUIDE.md](WEB_GUIDE.md)를 보세요.

CNBC · NBC News · BBC · Fox News · WSJ · CNN · NYT 기사를 매일 모아서 다음 일을 합니다.
**인공지능(AI)은 전혀 쓰지 않고**, 모든 처리를 규칙과 통계로만 합니다.

| 기능 | 하는 일 | 방법 (AI 없음) |
|---|---|---|
| 기사 수집 | 각 언론사 **공식 RSS**에서 제목·요약을 받고, 공개된 기사는 본문 앞부분도 가져옴 | 표준 HTTP 요청 + XML/HTML 파싱 |
| 순위 | 여러 매체가 함께 다룬 사건을 위로 올림 | TF-IDF 코사인 유사도로 같은 사건 묶기 → 점수 공식 |
| 브리핑 기사 | 그날 흐름을 분야별로 정리한 영문 브리핑 | TextRank로 핵심 문장 추출 + 고정 문장 틀로 연결 |
| 지문·질문 | 상위 기사로 지문 N개, 지문당 질문 M개 | 기사 앞부분 발췌 + 분야별 질문 템플릿 |
| 단어장 | 지문의 어려운 단어·표현과 한국어 뜻 | 기본 단어 목록 대조 + 빈도 점수 + 내장 용어집 |
| 첨삭 | 문법·어색한 표현 교정, 더 나은 표현 제안, 점수 | 한국인 학습자 오류 규칙 90여 개 + 점수 공식 |
| 학습 리포트 | 하루 지문·질문 수, 점수 추이, 반복 실수, 학습 방향 | 기록 집계 + 규칙 기반 조언 |

---

## 1. 준비물

- **Python 3.9 이상** 하나만 있으면 됩니다. 추가로 설치할 패키지는 없습니다.
  - Windows: https://www.python.org/downloads/ 에서 설치. 설치 첫 화면에서 **"Add python.exe to PATH"에 꼭 체크**하세요.
  - macOS: 터미널에서 `python3 --version`을 입력해 3.9 이상이면 그대로 쓰면 됩니다. 없으면 위 주소에서 설치하세요.
- 음성으로 답하기를 쓰려면 **Chrome** 브라우저를 권장합니다.

## 2. 실행

### Windows
1. 압축을 푼 `newsdesk` 폴더를 엽니다.
2. `start_windows.bat`을 더블클릭합니다.
3. 브라우저가 자동으로 열리고 `http://localhost:8765` 화면이 나옵니다. 처음 실행하면 바로 뉴스 수집을 시작합니다(1~2분).
4. 끝낼 때는 검은 창에서 `Ctrl + C`를 누르거나 창을 닫습니다.

### macOS
1. `start_mac.command`를 더블클릭합니다. "확인되지 않은 개발자" 경고가 뜨면 파일을 **우클릭 → 열기**를 누릅니다.
2. 또는 터미널에서:
   ```bash
   cd 내려받은위치/newsdesk
   python3 app.py
   ```

### 명령어 정리
```bash
python app.py            # 앱 실행 + 브라우저 열기 (오늘 뉴스가 없으면 자동 수집)
python app.py fetch      # 화면 없이 뉴스만 수집해서 저장 (예약 실행용)
python app.py demo       # 인터넷 없이 sample/ 폴더의 예시 기사로 체험
python app.py --port 9000 --no-browser   # 포트 바꾸기, 브라우저 자동 열기 끄기
```
(macOS·Linux는 `python` 대신 `python3`)

## 3. 화면별 사용법

- **브리핑**: 오늘의 순위 10개(점수, 보도 매체 수, 기사 수)와 분야별 영문 브리핑. `▶ 듣기`는 브라우저 내장 음성으로 읽어 줍니다. 원문 링크로 기사 전체를 볼 수 있어요.
- **지문·영작**: 지문을 읽고 질문에 답합니다. `표현 힌트 보기`로 써 볼 문형을 확인하고, 타이핑하거나 `🎙 말로 답하기`로 말한 뒤 `첨삭 받기`.
  - 결과: 종합·문법·어휘·자연스러움·내용 점수, 교정 목록(원래 표현 → 고친 표현 + 한국어 설명), 교정한 답변, 표현까지 다듬은 버전, 다음에 써 볼 표현, 팁.
  - `고쳐서 다시 쓰기`로 같은 질문에 여러 번 도전할 수 있고, 모든 시도가 기록됩니다.
- **단어장**: 오늘의 단어·표현(뜻·예문·빈도). ☆를 누르면 내 단어장에 저장, `외웠어요`로 관리.
- **리포트**: 연속 학습일, 최근 14일 학습일, 날짜별 지문(읽음/전체)·질문(답변/전체), 점수 그래프, 자주 나온 오류, 반복되는 실수와 예시, 개선 방향, 7일 계획, 설정 추천.
- **설정**: 하루 지문 수(1~10), 지문당 질문 수(1~5), 지문 길이, 답변 목표 분량, 음성 입력 버튼, 읽기 속도.
  설정을 바꾼 뒤 지문·영작 탭의 `다시 만들기`를 누르면 바로 적용됩니다.

## 4. 매일 자동 수집

앱이 켜져 있으면 매일 `config.json`의 `daily_fetch_time`(기본 07:00)에 자동으로 수집하고, 앱을 켤 때 오늘 뉴스가 없으면 바로 수집합니다.
앱을 켜 두지 않아도 매일 받으려면 운영체제 예약 기능으로 `python app.py fetch`를 실행하게 하세요.

### Windows (작업 스케줄러)
명령 프롬프트(cmd)에서 한 줄 입력 (경로는 본인 폴더로 바꾸세요):
```bat
schtasks /create /tn "DailyNewsEnglish" /sc daily /st 07:00 /tr "cmd /c cd /d C:\Users\내이름\newsdesk && python app.py fetch"
```
- 확인: `schtasks /query /tn "DailyNewsEnglish"`
- 지금 한 번 실행: `schtasks /run /tn "DailyNewsEnglish"`
- 삭제: `schtasks /delete /tn "DailyNewsEnglish" /f`

### macOS / Linux (cron)
1. 터미널에서 `which python3`로 파이썬 경로를 확인합니다(예: `/usr/bin/python3`).
2. `crontab -e` 입력 후 아래 줄을 추가하고 저장합니다:
   ```
   0 7 * * * cd /Users/내이름/newsdesk && /usr/bin/python3 app.py fetch >> data/fetch.log 2>&1
   ```
3. macOS에서 cron이 폴더에 접근하지 못하면 **시스템 설정 → 개인정보 보호 및 보안 → 전체 디스크 접근 권한**에 `/usr/sbin/cron`을 추가합니다.

## 5. 동작 원리 자세히

### 5-1. 순위 매기기 (`core/rank.py`)
1. 지난 36시간 기사만 사용합니다.
2. 기사마다 제목(2배 가중)+요약에서 불용어를 빼고 원형으로 바꾼 단어로 TF-IDF 벡터를 만듭니다.
3. 피드 상단 기사부터 차례로, 기존 묶음과의 코사인 유사도가 0.22 이상이면 같은 사건으로 묶습니다(고유명사 2개 이상 겹치면 +0.15). 제목만 있는 기사(CNN)는 핵심어 2개 이상 겹치는 묶음에 붙입니다.
4. 점수 = **3 × 보도한 매체 수** + 1 × log(기사 수+1) + 2 × 피드 상단 노출 + 1.5 × 최신성(12시간마다 절반) + 관심 분야 가중치.
5. 가중치와 관심 분야(`category_preference`)는 `config.json`에서 바꿀 수 있습니다. 예: 시장 뉴스를 더 보고 싶으면 `"Markets": 2.0`.

### 5-2. 브리핑 (`core/digest.py`)
- 각 사건의 모든 문장을 TextRank(문장끼리 핵심어를 많이 공유할수록 중요)로 점수 매기고, 비슷한 문장은 건너뛰며 2~3개를 고릅니다.
- 분야별 소제목 아래에 "On the markets front, CNBC reports: …"처럼 고정 연결 문구와 출처를 붙입니다.
- 첫 문단은 숫자로 만든 개요(몇 개 매체, 가장 많이 보도된 기사, 많이 나온 단어), 마지막은 will/next week/expected to가 들어간 문장을 모은 What to Watch입니다.
- 문장은 언론사 원문(요약문·본문 앞부분)에서 그대로 가져온 것이고, 출처를 함께 표시합니다.

### 5-3. 지문·질문 (`core/digest.py`, `core/questions.py`)
- 지문: 본문을 확보한 기사가 있으면 그 앞부분을 설정 길이만큼(문장 단위로) 자르고, 없으면 여러 매체의 핵심 문장을 모읍니다.
- 질문: 의견·감정·비즈니스·전망·한국과 비교·내 경험 6종 템플릿 중 분야에 맞는 순서로 고릅니다. 날짜와 기사 번호로 고정해서 같은 날에는 같은 질문이 나옵니다.

### 5-4. 단어장 (`core/vocab.py`, `core/glossary.py`)
- 일상 기본 단어 약 900개·불용어 목록에 없는 4글자 이상 단어만 후보로 삼고, 대문자로만 나오는 단어(사람·회사 이름)는 뺍니다.
- 점수 = 등장 횟수 + 단어 길이 + 용어집에 있으면 +3 + 여러 기사에 나오면 가산.
- 2단어 표현(콜로케이션)은 2번 이상 나오거나 용어집에 있으면 포함합니다.
- 한국어 뜻은 내장 용어집(시장·경제·정치·국제·감정 표현 약 250개)과 **`my_glossary.tsv`**(직접 추가)에서 찾고, 없으면 네이버 사전 링크를 보여 줍니다.
  `my_glossary.tsv`는 메모장으로 열어 `영어[Tab]뜻` 형식으로 한 줄씩 추가하세요.

### 5-5. 첨삭 (`core/grammar.py`, `core/scoring.py`)
규칙 하나하나에 한국어 설명이 붙어 있습니다. 주요 규칙:
- **수 일치**: he/she/it·everyone·the company + 동사원형(He want → wants), people is → are, there is many → there are, every days → every day, one of the reason → reasons, many flights was → were
- **시제**: yesterday/last week/ago가 있는 문장의 현재형(I go → went), if절의 will, 조동사·to 뒤 과거형, 불규칙 과거형(rised → rose 등 65개)
- **관사**: a/an을 철자가 아닌 발음 기준으로(a hour → an hour, an university → a university)
- **전치사·구조**: discuss about, mention about, contact to, attend to the meeting, marry with, since three years → for, look forward to see → seeing, explain me, suggest me to, let/make me to, despite of, depend of
- **단어 선택·콩글리시**: I'm interesting in, I am agree, more better, the most best, do a mistake, price is expensive, go to home, almost people, handphone, fighting, eye shopping, my condition is bad 등
- **문장**: 문장 첫 대문자, i → I, 축약형 아포스트로피(cant → can't), 띄어쓰기, 단어 반복, 35단어 넘는 긴 문장, although…but, Because로만 끝나는 문장
- **표현 제안**: very good → excellent처럼 very + 형용사를 한 단어로, I think·a lot of·thing·good/bad 반복
- **철자**: 자주 틀리는 철자 85개 + (macOS/Linux) `/usr/share/dict/words` 사전에 없는 단어 표시
- 하나를 고치면 드러나는 오류(thousands flights was → thousands of flights → were)를 잡기 위해 교정본을 최대 두 번 다시 검사합니다.
- 음성으로 답한 경우 대문자·구두점 오류는 음성 인식 탓이므로 빼고 채점합니다.

**점수 공식**
- 문법 = 10 − 0.8 × (100단어당 문법 오류) − 0.15 × (100단어당 대문자·구두점 오류)
- 자연스러움 = 10 − 0.9 × (100단어당 연어·단어 선택·구조 문제) − 표현 제안 수 × 0.4(최대 4개)
- 어휘 = 2 + 4 × (고급 단어 비율 ÷ 25%, 최대 1) + 2 × (단어 다양성) + 2 × (지문 단어 활용, 3개면 만점)
- 내용 = 2 + 3 × 분량 달성률 + 1.5 × 문장 수(3문장 만점) + 1.5 × 연결어(2개 만점) + 의견·감정 표현 1 + 지문 주제어 활용 1
- 종합 = 문법 30% + 어휘 25% + 자연스러움 25% + 내용 20%

### 5-6. 리포트 (`core/report.py`)
- 질문별 마지막 시도만 점수에 반영하고, 시도 횟수는 따로 셉니다.
- 오류 유형을 세어 많은 순서(대문자·구두점은 뒤로)대로 '반복되는 실수'와 실제 예시를 보여 줍니다.
- 최근 14일 학습일, 하루 평균 문항 수(설정 대비), 전반부·후반부 평균 점수 차이, 가장 약한 영역으로 개선 방향 문장을 만들고, 오류 유형별 연습법으로 7일 계획을 짭니다.

## 6. 선택 기능

### LanguageTool 연동 (규칙 기반 오픈소스 문법 검사기)
더 많은 문법 규칙(수천 개)을 쓰고 싶으면 `config.json`에서:
```json
"languagetool": {"enabled": true, "url": "https://api.languagetool.org/v2/check", "language": "en-US"}
```
- LanguageTool도 AI가 아닌 규칙 기반 검사기입니다. 설명은 영어로 표시됩니다(`[LanguageTool]` 표시).
- 공개 서버를 쓰면 **답변 글이 languagetool.org로 전송**됩니다. 글을 밖으로 보내기 싫으면 LanguageTool을 내 컴퓨터에 설치해(Java 필요) `"url": "http://localhost:8081/v2/check"`로 바꾸세요.
- 공개 서버는 무료 사용량 제한이 있습니다(분당 요청 수 등).

### 철자 사전
`"wordlist_path"`에 단어 목록 파일(한 줄에 한 단어)을 지정하면 사전에 없는 단어를 표시합니다. macOS·Linux에는 `/usr/share/dict/words`가 있어 기본으로 켜집니다. Windows는 영어 단어 목록 파일을 구해서 경로를 넣으면 됩니다.

### 매체·피드 바꾸기
`config.json`의 `feeds` 목록에서 주소를 추가·삭제하거나 `"enabled": false`로 끌 수 있습니다.
- **CNN**: 공식 RSS가 2024년 이후 갱신되지 않아 Google News의 `site:cnn.com` 검색 피드를 씁니다. 제목만 오기 때문에 순위·브리핑에는 반영되지만 본문은 다른 매체 것을 씁니다.
- **WSJ**: 예전 주소(feeds.a.dj.com)가 멈춰 새 주소 `feeds.content.dowjones.io`를 씁니다.
- **WSJ·NYT**는 유료 구독 기사라 본문은 가져오지 않고 RSS 요약만 씁니다(`no_full_text_outlets`).

## 7. 문제 해결

| 증상 | 해결 |
|---|---|
| `python`을 찾을 수 없음 (Windows) | 파이썬을 다시 설치하며 "Add python.exe to PATH" 체크. 또는 `py app.py`로 실행 |
| 수집 결과가 0건 | 인터넷 연결 확인. 회사망이면 프록시 때문에 막힐 수 있어요. 화면의 수집 로그에서 `!` 표시된 피드 주소를 확인 |
| 특정 매체만 안 들어옴 | 그 매체의 RSS 주소가 바뀐 경우입니다. config.json에서 주소 수정 |
| 마이크 버튼이 없음 | Chrome/Edge에서 열어 주세요. 설정 탭에서 '보이기'인지 확인 |
| 포트 사용 중 오류 | `python app.py --port 9000` |
| 기록 초기화 | 앱을 끄고 `data/newsdesk.db` 파일 삭제 |

## 8. 알아 둘 점

- 규칙 기반이라 **규칙에 없는 오류는 못 잡습니다.** 특히 고유명사 주어(Nvidia need → needs), 복잡한 시제, 문맥상 어색한 단어는 놓칠 수 있어요. 대신 잡은 오류는 왜 틀렸는지 항상 설명할 수 있습니다.
- "원어민 버전"처럼 새 문장을 지어내는 기능은 없습니다. 대신 '표현까지 다듬은 버전'(규칙 교정 + 표현 업그레이드 적용)과 문형 제안을 줍니다.
- 브리핑은 언론사 문장을 골라 엮은 것이라 문장 간 연결이 사람이 쓴 기사만큼 매끄럽지는 않습니다.
- 음성 입력은 브라우저 내장 음성 인식을 씁니다. Chrome에서는 음성이 Google 서버에서 인식되므로 이 부분만은 기계학습 기술입니다. 원치 않으면 설정에서 숨기세요. 읽어 주기(▶ 듣기)는 컴퓨터에 설치된 음성을 씁니다.
- 기사 본문은 **개인 학습용으로만** 쓰세요. 다른 사람에게 배포하거나 공개 웹에 올리면 저작권 문제가 될 수 있습니다.

## 9. 폴더 구성
```
newsdesk/
├─ app.py              실행 파일 (서버 + 명령어)
├─ config.json         피드 주소, 순위 가중치, 수집 시간, 검사기 설정
├─ my_glossary.tsv     나만의 용어집
├─ start_windows.bat   Windows 실행
├─ start_mac.command   macOS 실행
├─ core/
│  ├─ feeds.py         RSS 수집·본문 추출
│  ├─ rank.py          같은 사건 묶기·순위
│  ├─ digest.py        브리핑·지문 만들기
│  ├─ questions.py     질문 템플릿·표현 은행
│  ├─ vocab.py         단어장 추출
│  ├─ glossary.py      내장 용어집(한국어 뜻)
│  ├─ grammar.py       첨삭 규칙
│  ├─ scoring.py       점수·피드백
│  ├─ report.py        학습 리포트
│  ├─ textutil.py      문장·단어 처리, 기본 단어 목록
│  └─ store.py         SQLite 저장
├─ static/index.html   화면 (로컬 버전)
├─ build_site.py       웹 버전 데이터 만들기 (GitHub Actions가 매일 실행)
├─ docs/               웹 버전 사이트 (GitHub Pages가 공개하는 폴더)
├─ .github/workflows/daily.yml  매일 자동 실행 설정
├─ WEB_GUIDE.md        웹 버전 설치 안내
├─ sample/             인터넷 없이 체험용 예시 피드
└─ data/newsdesk.db    내 기록 (처음 실행 때 생김)
```
