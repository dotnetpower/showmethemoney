# VS Code 디버깅 가이드

## 🐛 디버깅 구성

### 사용 가능한 디버깅 설정

#### 1. Python: FastAPI (권장)
FastAPI 서버를 디버깅 모드로 실행합니다.

**사용법:**
1. `F5` 키 또는 "실행 및 디버그" 패널에서 선택
2. 브레이크포인트 설정: 코드 왼쪽 여백 클릭
3. API 호출 시 자동으로 브레이크포인트에서 멈춤

**특징:**
- 자동 재시작 (`--reload`)
- 포트 8000에서 실행
- 환경변수 자동 로드

#### 2. Python: Current File
현재 열려있는 Python 파일을 직접 실행합니다.

**사용법:**
1. 디버깅할 `.py` 파일 열기
2. `F5` 선택 → "Python: Current File" 선택

#### 3. Python: Pytest
테스트 코드를 디버깅합니다.

**사용법:**
1. 테스트 파일 열기
2. `F5` → "Python: Pytest" 선택

#### 4. Python: Attach
이미 실행 중인 Python 프로세스에 연결합니다.

**사용법:**
1. 먼저 코드에 다음 추가:
```python
import debugpy
debugpy.listen(5678)
debugpy.wait_for_client()
```
2. 프로그램 실행
3. VS Code에서 "Python: Attach" 선택

## 📋 VS Code 태스크

### 빠른 실행 (Ctrl+Shift+B 또는 Cmd+Shift+B)

#### Start All Services (기본)
Backend와 Frontend를 동시에 실행합니다.

#### 개별 서비스
- **Backend: Start Server** - FastAPI 서버만 실행
- **Frontend: Start Dev Server** - React 개발 서버만 실행
- **Frontend: Build Production** - 프로덕션 빌드

#### 개발 도구
- **Python: Install Dependencies** - 패키지 설치
- **Python: Run Tests** - 테스트 실행
- **Python: Format Code** - Black으로 포맷팅
- **Python: Lint Code** - Ruff로 린트 검사
- **Verify System** - 시스템 검증

### 태스크 실행 방법
1. `Ctrl+Shift+P` (또는 `Cmd+Shift+P`)
2. "Tasks: Run Task" 입력
3. 원하는 태스크 선택

## 🔧 단축키

### 디버깅
- `F5` - 디버깅 시작/계속
- `F9` - 브레이크포인트 토글
- `F10` - 단계 넘기기 (Step Over)
- `F11` - 단계 들어가기 (Step Into)
- `Shift+F11` - 단계 나가기 (Step Out)
- `Shift+F5` - 디버깅 중지
- `Ctrl+Shift+F5` - 디버깅 재시작

### 편집
- `Ctrl+Shift+P` - 명령 팔레트
- `Ctrl+P` - 파일 빠르게 열기
- `Ctrl+Shift+F` - 전체 검색
- `Ctrl+/` - 주석 토글
- `Alt+↑/↓` - 라인 이동
- `Shift+Alt+↑/↓` - 라인 복사

## 💡 디버깅 팁

### 1. 조건부 브레이크포인트
브레이크포인트 우클릭 → "Edit Breakpoint" → 조건 입력
```python
symbol == "AAPL"
```

### 2. 로그포인트
브레이크포인트 우클릭 → "Edit Breakpoint" → "Logpoint"
```
Stock {symbol}: price={quote.c}
```

### 3. 변수 감시
"Watch" 패널에서 변수나 표현식 추가

### 4. 호출 스택 확인
"Call Stack" 패널에서 함수 호출 순서 확인

### 5. 디버그 콘솔 사용
하단 "Debug Console"에서 실시간으로 Python 코드 실행

## 🎯 실전 예제

### FastAPI 엔드포인트 디버깅

1. `src/api/stocks.py` 파일 열기
2. `get_stock_detail` 함수에 브레이크포인트 설정
3. `F5` → "Python: FastAPI" 선택
4. 브라우저에서 `http://localhost:8000/api/stocks/AAPL` 접속
5. VS Code에서 브레이크포인트에 멈춤
6. 변수 값 확인 및 단계별 실행

### Semantic Kernel 에이전트 디버깅

1. `src/agent/agent_service.py` 열기
2. `chat` 메서드에 브레이크포인트
3. `F5` → "Python: FastAPI" 실행
4. Frontend 채팅 인터페이스에서 메시지 전송
5. 에이전트 실행 흐름 단계별 추적

### 비동기 코드 디버깅

```python
async def get_stock_detail(symbol: str):
    # 브레이크포인트 여기 설정
    finnhub = get_finnhub_client()
    
    # F10으로 다음 줄로
    profile = finnhub.get_company_profile(symbol.upper())
    
    # F11로 함수 내부로
    quote = finnhub.get_quote(symbol.upper())
    
    return {...}
```

## 🔍 문제 해결

### 브레이크포인트가 작동하지 않을 때
1. `justMyCode: false` 설정 확인
2. 가상환경이 올바른지 확인
3. 파일이 저장되었는지 확인

### 환경변수가 로드되지 않을 때
1. `.env` 파일이 있는지 확인
2. `python.envFile` 설정 확인
3. VS Code 재시작

### 디버거 연결 실패
1. 포트 충돌 확인 (`lsof -i :8000`)
2. 방화벽 설정 확인
3. 다른 프로세스 종료 후 재시도

## 📚 추가 리소스

- [VS Code Python 디버깅 문서](https://code.visualstudio.com/docs/python/debugging)
- [FastAPI 디버깅 가이드](https://fastapi.tiangolo.com/tutorial/debugging/)
- [debugpy 문서](https://github.com/microsoft/debugpy)
