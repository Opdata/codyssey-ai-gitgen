# ai-gitgen — AI 기반 Git 커밋/PR 초안 생성기

## 설치 및 실행 방법
Python 3.10 이상과 Git이 필요합니다. 외부 패키지를 쓰지 않으므로 별도 설치 과정은 없습니다.

```bash
git clone https://github.com/Opdata/codyssey-ai-gitgen.git
```

실행은 **커밋/PR 초안을 만들 대상 Git 저장소의 루트 디렉토리**에서 합니다.
```bash
cd <대상 저장소 루트>
python3 <clone 경로>/codyssey-ai-gitgen/main.py commit
```

## 환경변수(API Key) 설정 방법
> 지원 환경: macOS (zsh)

API Key는 **환경변수 `AI_API_KEY`로만** 전달합니다. 코드나 저장소 파일에 키를 적지 마세요.
한 번 커밋된 키는 파일을 지워도 Git 히스토리에 남아, push 시 그대로 노출됩니다.

Gemini API Key는 [Google AI Studio](https://aistudio.google.com)에서 발급합니다.

### 방법 1. 현재 터미널에서만 사용
```bash
export AI_API_KEY="YOUR_KEY"
```
- `export`로 설정한 값은 **그 터미널 창에서만** 유지됩니다.
- 터미널을 닫거나 새 창을 열면 사라지므로 다시 입력해야 합니다.

### 방법 2. 영구 설정 (권장: 매번 입력하지 않아도 됨)
zsh는 터미널을 열 때마다 `~/.zshrc`를 자동으로 실행합니다. 여기에 등록하면 새 터미널에서도 자동 설정됩니다.
```bash
echo 'export AI_API_KEY="YOUR_KEY"' >> ~/.zshrc   # >> : 파일 끝에 추가 (> 는 덮어쓰기이므로 사용 금지)
source ~/.zshrc                                   # 현재 터미널에도 즉시 반영
```
- 키는 홈 디렉토리 설정 파일에 저장되므로 프로젝트 저장소에 포함되지 않습니다.
- 키를 바꾸려면 `~/.zshrc`에서 해당 줄을 수정한 뒤 `source ~/.zshrc`를 다시 실행합니다.

### 설정 확인
```bash
echo ${AI_API_KEY:+설정됨}   # "설정됨"이 출력되면 성공 (키 값은 화면에 노출되지 않음)
```
키가 없으면 실행 시 아래 메시지가 출력되고 종료됩니다.
```
[ERROR] AI_API_KEY 환경변수가 설정되지 않았습니다.
```

## 사용 예시
대상 저장소 루트에서 실행합니다. (`TOOL` = clone한 `main.py` 경로)
```bash
TOOL=<clone 경로>/codyssey-ai-gitgen/main.py
python3 $TOOL commit                     # 커밋 메시지 생성
python3 $TOOL pr                         # PR 제목/본문 생성
python3 $TOOL pr --safe-mode             # 민감정보 마스킹 후 전송
python3 $TOOL commit --temperature 0     # 파라미터 변경 (--model, --temperature, --max-tokens)
python3 $TOOL commit --help              # 옵션과 기본값 확인
```

## 출력 예시
### 커밋 메시지
```
[INFO] Git status 수집 완료: 2개 파일 변경 감지
[INFO] Git diff 수집 완료: 22줄
[INFO] AI API 요청 중... (model=gemini-3.1-flash-lite, temperature=0.2, max_tokens=500)
[INFO] API 호출 횟수: 1
[DONE] 커밋 메시지 생성 완료

--- Commit Message ---
feat: 계산기 기능 및 설정 파일 추가

- calc.py에 덧셈 및 나눗셈 연산 함수 구현
- config.py에 API 키 및 관리자 이메일 설정 추가
----------------------------------------
```

### PR 제목/본문
```
[INFO] Git status 수집 완료: 2개 파일 변경 감지
[INFO] Git diff 수집 완료: 22줄
[INFO] 현재 브랜치: main
[INFO] AI API 요청 중... (model=gemini-3.1-flash-lite, temperature=0.2, max_tokens=500)
[INFO] API 호출 횟수: 1
[DONE] PR 초안 생성 완료

--- PR Title ---
계산기 기능 구현 및 설정 파일 추가

--- PR Body ---
## Why
- 프로젝트에 필요한 기본 연산 기능과 환경 설정 정보가 필요함

## What
- `calc.py` 파일에 덧셈(`add`) 및 나눗셈(`div`) 함수 구현
- `config.py` 파일에 `API_KEY` 및 `ADMIN_EMAIL` 설정값 추가

## How to Test
- `calc.py`를 임포트하여 `add(1, 2)` 호출 시 3이 반환되는지 확인
- `div(10, 0)` 호출 시 `ValueError`가 발생하는지 확인
- `config.py`에서 정의된 변수들이 정상적으로 로드되는지 확인
----------------------------------------
```

## 주의사항: 민감정보와 safe-mode
`git diff` 내용은 외부 AI API(Gemini)로 전송됩니다. Gemini 무료 티어는 전송된 내용을 Google 제품 개선에 사용할 수 있으므로, diff에 API Key나 개인정보가 섞이지 않도록 주의하세요.

`--safe-mode`를 사용하면 전송 전에 아래 패턴을 마스킹합니다.

| 대상 | 예시 | 변환 결과 |
|---|---|---|
| 이름이 붙은 비밀값 (api_key, secret, token, password) | `API_KEY = "abc123"` | `API_KEY = "[MASKED]"` |
| Google / OpenAI / AWS 키 형식 | `AIza...`, `sk-...`, `AKIA...` | `[MASKED_API_KEY]`, `[MASKED_AWS_KEY]` |
| 이메일 | `admin@company.com` | `[MASKED_EMAIL]` |

```
[INFO] safe-mode: 민감정보 2건 마스킹
```
마스킹은 알려진 패턴만 처리하므로 완전하지 않습니다. 키나 개인정보가 담긴 파일은 `.gitignore`로 제외해 애초에 커밋하지 않는 것이 우선입니다.

## 다른 맥에서 테스트하기 (빠른 세팅)
Python 3.10 이상과 Git이 설치된 맥 기준입니다. 터미널 창 하나에서 순서대로 실행합니다.

**1. API Key 설정** (현재 터미널에서만 유효)
```bash
export AI_API_KEY="YOUR_KEY"
```

**2. 도구 받기 + 테스트용 저장소 만들기** (통째로 붙여넣기)
```bash
cd ~ && git clone https://github.com/Opdata/codyssey-ai-gitgen.git 2>/dev/null; cd ~/codyssey-ai-gitgen && git pull -q
TOOL=~/codyssey-ai-gitgen/main.py
rm -rf ~/demo-repo && mkdir ~/demo-repo && cd ~/demo-repo && git init -q -b main
git -c user.name=demo -c user.email=demo@example.com commit -q --allow-empty -m init
git checkout -q -b feature/calc
printf 'def add(a, b):\n    return a + b\n\n\ndef div(a, b):\n    if b == 0:\n        raise ValueError("0으로 나눌 수 없음")\n    return a / b\n' > calc.py
printf 'API_KEY = "my-secret-value-123"\nADMIN_EMAIL = "admin@company.com"\n' > config.py
git add . && git status --short && python3 --version
```
`A  calc.py`, `A  config.py`와 Python 버전이 출력되면 준비 완료입니다. (`config.py`의 키/이메일은 safe-mode 확인용 가짜 값입니다.)

**3. 실행**
```bash
python3 $TOOL commit
python3 $TOOL pr
python3 $TOOL pr --safe-mode
(unset AI_API_KEY; python3 $TOOL commit)   # API Key 미설정 상황 확인
```
API Key 미설정 확인 시 `env -u AI_API_KEY python3 ...`는 zsh의 `python3` 별칭을 거치지 않아 macOS 기본 Python(3.9)이 실행될 수 있으므로, 위처럼 괄호(서브셸) 안에서 `unset`을 사용합니다.
