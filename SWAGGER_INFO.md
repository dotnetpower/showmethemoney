# Swagger UI 접속 방법

FastAPI 서버를 실행한 후 다음 URL로 접속하세요:

## Swagger UI (Interactive API Documentation)
```
http://localhost:8000/docs
```

## ReDoc (Alternative Documentation)
```
http://localhost:8000/redoc
```

## OpenAPI JSON Schema
```
http://localhost:8000/openapi.json
```

## 주요 기능

### Swagger UI에서 할 수 있는 것:
- 모든 API 엔드포인트 확인
- 각 엔드포인트의 파라미터, 응답 형식 확인
- **Try it out** 버튼으로 직접 API 테스트
- 예제 요청/응답 확인

### 주요 엔드포인트:

1. **GET /api/v1/etf/all** - 전체 ETF 조회 (3,600개 이상)
2. **GET /api/v1/etf/list/{provider}** - 특정 운용사 ETF 조회
3. **GET /api/v1/etf/list** - 운용사별 ETF 목록
4. **POST /api/v1/etf/update** - 전체 데이터 업데이트
5. **GET /health** - 헬스 체크

## 서버 실행

```bash
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

또는 VS Code Task 사용:
```
Backend: Start Server
```
