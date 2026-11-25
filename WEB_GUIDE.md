# 웹 버전 설치 안내 (GitHub Pages + GitHub Actions, AI 미사용)

웹 버전은 **내 컴퓨터를 켜 두지 않아도** 매일 아침 뉴스가 갱신되고, 휴대폰·회사 PC 어디서든 주소 하나로 여는 방식입니다.

```
매일 07:05 (한국 시간)
 GitHub Actions ──▶ build_site.py 실행 (RSS 수집 → 순위 → 브리핑·지문·질문·단어장, 규칙 기반)
                └─▶ docs/data/날짜.json 저장
 GitHub Pages  ──▶ docs/ 폴더를 웹사이트로 공개 (https://내아이디.github.io/저장소이름/)
 내 브라우저   ──▶ 첨삭·리포트를 같은 Python 코드로 브라우저 안에서 계산 (Pyodide)
                └─▶ 답변·점수·단어장은 이 브라우저에 저장 (백업 파일로 옮기기 가능)
```

비용은 들지 않습니다. 공개(Public) 저장소는 GitHub Actions와 Pages를 무료로 쓸 수 있어요.

---

## 1단계. GitHub 가입
1. https://github.com 접속 → **Sign up**.
2. 이메일, 비밀번호, 사용자 이름(아이디)을 정합니다. 이 아이디가 사이트 주소에 들어갑니다 (`아이디.github.io`).
3. 이메일 인증까지 마칩니다.

## 2단계. 저장소(Repository) 만들기
1. 오른쪽 위 **+** → **New repository**.
2. **Repository name**: `news-english` (원하는 이름 가능. 영어 소문자·하이픈 권장)
3. **Public** 선택. (Private 저장소의 Pages는 유료 요금제에서만 됩니다.)
4. 다른 옵션(README 추가 등)은 체크하지 않고 **Create repository**.

## 3단계. 파일 올리기
1. 만든 저장소 화면에서 **uploading an existing file** 링크(또는 **Add file → Upload files**)를 누릅니다.
2. 압축을 푼 `newsdesk` 폴더를 열고, **폴더 안의 내용물 전체**(app.py, build_site.py, config.json, core, docs, sample, static 등)를 선택해 브라우저 창으로 끌어다 놓습니다. `newsdesk` 폴더 자체가 아니라 그 안의 것들입니다.
3. 아래쪽 **Commit changes** 클릭.
4. **`.github` 폴더 확인 (중요)**: 이름이 점(.)으로 시작하는 폴더는 Mac·Windows에서 숨김 처리돼 업로드에서 빠지는 경우가 많습니다. 저장소 첫 화면에 `.github` 폴더가 안 보이면 이렇게 직접 만드세요:
   1. **Add file → Create new file**
   2. 파일 이름 칸에 `.github/workflows/daily.yml` 을 그대로 입력 (슬래시를 치면 폴더가 자동으로 만들어집니다)
   3. 압축 파일 안 `newsdesk/.github/workflows/daily.yml` 내용을 메모장으로 열어 전부 복사해 붙여넣기
   4. **Commit changes**
5. `docs` 폴더 안의 `.nojekyll` 파일도 같은 이유로 빠질 수 있습니다. 없으면 **Add file → Create new file**에서 이름을 `docs/.nojekyll`로 하고 내용은 비운 채 저장하세요.

## 4단계. Actions에 쓰기 권한 주기
매일 수집한 뉴스를 저장소에 저장하려면 권한이 필요합니다.
1. 저장소 위쪽 **Settings** 탭 → 왼쪽 메뉴 **Actions → General**.
2. 아래로 내려 **Workflow permissions**에서 **Read and write permissions** 선택 → **Save**.

## 5단계. GitHub Pages 켜기
1. **Settings** → 왼쪽 메뉴 **Pages**.
2. **Build and deployment → Source**: **Deploy from a branch**.
3. **Branch**: `main`, 폴더: `/docs` → **Save**.
4. 1~2분 뒤 같은 화면 위쪽에 사이트 주소가 나타납니다: `https://아이디.github.io/news-english/`
   이 시점에는 예시(sample) 뉴스가 보입니다.

## 6단계. 첫 수집 실행
1. 저장소 위쪽 **Actions** 탭. "workflows aren't being run" 같은 안내가 나오면 **I understand my workflows, go ahead and enable them** 클릭.
2. 왼쪽 목록에서 **Daily news** → 오른쪽 **Run workflow** → 초록색 **Run workflow**.
3. 1~3분 뒤 초록색 체크가 뜨면 성공입니다. 빨간 X가 뜨면 눌러서 로그를 보세요(아래 문제 해결 참고).
4. 다시 1~2분 뒤(Pages 반영 시간) 사이트를 새로고침하면 오늘 실제 뉴스가 나옵니다.
5. 이후로는 **매일 한국 시간 7시 5분경 자동 실행**됩니다. GitHub 서버 사정으로 몇 분~수십 분 늦어질 수 있어요.

## 7단계. 휴대폰에서 앱처럼 쓰기 (홈 화면에 추가)
모바일 화면에서는 탭이 아래쪽 바(📰 브리핑 · ✍️ 지문·영작 · 📚 단어장 · 📈 리포트 · ⚙️ 설정)로 바뀌고, 답을 입력하는 동안에는 키보드를 가리지 않게 탭바가 숨겨집니다. 홈 화면에 추가하면 주소창 없이 앱처럼 열리고, 한 번 본 뉴스는 인터넷이 끊겨도 다시 볼 수 있어요.

**iPhone (Safari)**
1. Safari로 `https://catnipa.github.io/english/` 접속 (다른 브라우저 앱에서는 홈 화면 추가가 안 될 수 있어요)
2. 아래쪽 가운데 **공유 버튼**(네모에서 화살표가 위로 나온 모양)
3. 목록을 아래로 내려 **홈 화면에 추가**
4. 이름이 '외신영어'로 나오면 오른쪽 위 **추가**

**Android (Chrome)**
1. Chrome으로 사이트 접속
2. 오른쪽 위 **⋮** 메뉴 → **홈 화면에 추가** 또는 **앱 설치**
3. **설치**(또는 **추가**)를 누르면 앱 서랍과 홈 화면에 아이콘이 생깁니다

참고: 홈 화면 앱과 브라우저는 저장 공간이 따로일 수 있어요(특히 iPhone). 브라우저에서 쌓은 기록을 홈 화면 앱으로 옮기려면 설정 탭의 **백업 파일 내려받기 → 백업 불러오기**를 쓰세요.

---

## 쓰는 법 (로컬 버전과 같음)
- **브리핑 / 지문·영작 / 단어장 / 리포트 / 설정** 탭 구성은 로컬 버전과 같습니다.
- **처음 첨삭할 때** 브라우저가 첨삭 엔진(Pyodide, 약 10MB)을 한 번 내려받아 10~30초 걸립니다. 그 뒤로는 빠릅니다.
- **지문 수·질문 수 바꾸기**: 설정 탭에서 바꾼 뒤 지문·영작 탭의 **다시 만들기**를 누르면 그 날짜 지문이 내 설정으로 다시 만들어집니다(브라우저 안에서 계산).
- **기록은 이 브라우저에만 저장**됩니다. 휴대폰과 PC는 기록이 따로 쌓여요. 옮기려면 설정 탭 **백업 파일 내려받기** → 다른 기기에서 **백업 불러오기**. 브라우저의 사이트 데이터를 지우면 기록도 지워지니 가끔 백업하세요.
- 위쪽 **새로고침** 버튼은 GitHub에 올라온 최신 뉴스를 다시 확인합니다.

## 설정 바꾸기 (GitHub 웹에서 바로 수정)
저장소에서 파일을 누르고 연필(✏️ Edit) 아이콘 → 수정 → **Commit changes**. 다음 수집부터 반영됩니다.
- **수집 시간**: `.github/workflows/daily.yml`의 `cron: "5 22 * * *"`. UTC 기준이라 한국 시간에서 9시간을 뺍니다. 예: 한국 6시 30분 → `30 21 * * *`.
- **매체·피드 주소, 순위 가중치, 관심 분야**: `config.json` (로컬 버전 README 5-1, 6장 참고).
- **내 용어집**: `my_glossary.tsv`에 `영어[Tab]뜻` 한 줄씩.
- **보관 기간**: `daily.yml`의 `python build_site.py`를 `python build_site.py --keep-days 90`처럼 바꾸면 90일치를 남깁니다(기본 60일).

## 로컬 버전과 다른 점
| | 로컬 버전 | 웹 버전 |
|---|---|---|
| 실행 | 내 컴퓨터에서 `python app.py` | 주소만 열면 됨 (PC·휴대폰) |
| 뉴스 갱신 | 앱이 켜져 있을 때 / 예약 작업 | GitHub가 매일 자동 |
| 지문 내용 | 무료 기사는 **본문 앞부분** 사용 | **RSS 요약문만** 사용 (아래 이유) |
| 기록 저장 | 내 컴퓨터 파일(`data/newsdesk.db`) | 각 브라우저 (백업 파일로 이동) |
| LanguageTool 연동 | 가능 | 없음 (내장 규칙만) |
| 철자 사전 검사 | macOS·Linux에서 켜짐 | 없음 (자주 틀리는 철자 85개 목록은 동작) |

**지문이 RSS 요약문만 쓰는 이유**: GitHub Pages 사이트는 주소를 아는 누구나 볼 수 있는 공개 사이트입니다. 언론사 기사 본문을 그대로 공개 사이트에 올리면 저작권 문제가 될 수 있어서, 웹 버전은 언론사가 배포용으로 내놓은 RSS 제목·요약만 씁니다. 그래서 지문이 로컬 버전보다 짧을 수 있어요(여러 매체의 요약을 모아 구성). 긴 본문으로 공부하고 싶으면 로컬 버전을 쓰거나, 각 지문의 **원문 링크**를 눌러 기사 전체를 읽으세요. `config.json`의 `web_fetch_full_text`를 `true`로 바꾸면 본문도 넣지만, 그 경우 공개 사이트에 본문이 올라간다는 점을 감안해야 합니다.

## 내 컴퓨터에서 웹 버전 미리 보기
```bash
python build_site.py --offline sample      # 예시 데이터로 docs/ 만들기 (실제 뉴스는 --offline 없이)
python -m http.server 8000 --directory docs
```
브라우저에서 `http://localhost:8000` 접속. (파일을 더블클릭해서 열면 데이터를 못 불러오니 꼭 이렇게 여세요.)

## 문제 해결
| 증상 | 확인할 것 |
|---|---|
| Actions가 빨간 X, 로그에 `Permission denied` / `403` | 4단계 쓰기 권한 설정 |
| Actions 탭에 Daily news가 없음 | `.github/workflows/daily.yml`이 올라갔는지 (3단계 4번) |
| 사이트가 404 | ① Settings → Pages에서 Branch가 `main`으로 **저장**됐는지(None이면 아직 꺼진 상태) ② 저장 후 Actions 탭에 **pages build and deployment**가 초록색으로 끝났는지(보통 1~3분) ③ 주소가 `https://아이디.github.io/저장소이름/`인지 ④ 휴대폰은 캐시 때문에 늦게 바뀔 수 있으니 새로고침 |
| 사이트는 뜨는데 "아직 올라온 뉴스가 없어요" | 6단계 첫 실행 후 새로고침 |
| 매일 갱신이 멈춤 | Actions 탭에서 최근 실행 기록 확인. 공개 저장소에 60일간 활동이 없으면 GitHub가 예약 실행을 멈출 수 있어요. 매일 수집 커밋이 생기므로 보통은 괜찮지만, 멈췄다면 Actions 탭에서 다시 **Enable workflow** |
| 특정 매체가 빠짐 | 실행 로그에서 `!` 표시된 피드 주소를 `config.json`에서 수정 |
| 첨삭 버튼을 눌러도 오래 멈춤 | 처음 한 번은 엔진 다운로드(10~30초). 회사 네트워크가 cdn.jsdelivr.net을 막으면 첨삭이 안 될 수 있어요 |
| 마이크 버튼이 없음 | Chrome/Edge(PC·Android)에서 지원. iPhone Safari는 음성 인식 지원이 제한적이에요 |
