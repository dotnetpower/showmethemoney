# 보안 정책 (Security Policy)

## 지원되는 버전 (Supported Versions)

현재 다음 버전에 보안 업데이트를 제공합니다:

| 버전 | 지원 여부 |
| --- | --- |
| 1.0.x | :white_check_mark: |

## 보안 취약점 보고 (Reporting a Vulnerability)

보안 취약점을 발견하신 경우, GitHub Issues가 아닌 비공개 채널을 통해 보고해 주시기 바랍니다.

1. 프로젝트 관리자에게 직접 연락
2. 취약점에 대한 상세한 설명 제공
3. 재현 단계 포함 (가능한 경우)

보고하신 취약점은 24시간 내에 검토되며, 심각도에 따라 즉시 조치됩니다.

## 보안 조치 (Security Measures)

### 1. 인증 및 인가 (Authentication & Authorization)

- **API 키 인증**: 프로덕션 환경에서는 `API_KEY` 환경 변수를 설정하여 API 엔드포인트 보호
- **환경 변수**: 모든 민감한 정보는 환경 변수로 관리
- **개발 모드**: API 키가 설정되지 않은 경우 개발 모드로 동작 (프로덕션에서는 반드시 설정 필요)

```bash
# 프로덕션 환경 설정 예시
export API_KEY="your-secure-api-key-here"
export OPENAI_API_KEY="your-openai-api-key"
export APPLICATION_INSIGHTS_CONNECTION_STRING="your-connection-string"
```

### 2. 입력 검증 (Input Validation)

- **Path Traversal 방어**: 모든 파일 경로 입력에 대해 검증 수행
- **SQL/Command Injection 방어**: 파라미터화된 명령어 실행
- **XSS 방어**: 특수 문자 검증 및 차단
- **길이 제한**: 입력 데이터 길이 제한 (예: 커밋 메시지 500자)

### 3. CORS 설정 (Cross-Origin Resource Sharing)

- 허용된 도메인만 접근 가능
- `CORS_ORIGINS` 환경 변수로 관리
- 기본값: 개발 환경 (localhost) 및 프로덕션 도메인

```bash
# CORS 설정 예시
export CORS_ORIGINS="https://example.com,https://api.example.com"
```

### 4. Docker 보안 (Container Security)

- **비특권 사용자**: 컨테이너는 root가 아닌 `appuser`로 실행
- **최소 권한**: 필요한 최소한의 권한만 부여
- **읽기 전용 파일 시스템**: 가능한 경우 읽기 전용으로 마운트

### 5. 의존성 관리 (Dependency Management)

- 정기적인 의존성 업데이트
- 보안 취약점 스캔 (GitHub Dependabot 활용)
- 최신 안정 버전 사용

### 6. 민감 정보 보호 (Secrets Management)

- `.env` 파일은 Git에 커밋되지 않음 (`.gitignore`에 포함)
- 환경 변수를 통한 설정 관리
- 하드코딩된 비밀 정보 없음

### 7. 에러 처리 (Error Handling)

- 프로덕션 환경에서는 상세한 에러 정보 노출 방지
- 사용자에게는 일반적인 에러 메시지만 표시
- 상세 로그는 Application Insights에 기록

## 보안 체크리스트 (Security Checklist)

### 배포 전 확인사항

- [ ] `API_KEY` 환경 변수 설정
- [ ] `OPENAI_API_KEY` 환경 변수 설정 (Agent 사용 시)
- [ ] `APPLICATION_INSIGHTS_CONNECTION_STRING` 설정
- [ ] `CORS_ORIGINS` 프로덕션 도메인으로 설정
- [ ] `.env` 파일이 Git에 커밋되지 않는지 확인
- [ ] Docker 컨테이너가 비특권 사용자로 실행되는지 확인
- [ ] 최신 의존성 버전 사용
- [ ] 보안 테스트 통과 확인

### 정기 점검사항

- [ ] 의존성 보안 업데이트 확인 (월 1회)
- [ ] 접근 로그 검토 (주 1회)
- [ ] 비정상적인 API 호출 패턴 모니터링
- [ ] SSL/TLS 인증서 만료일 확인

## 알려진 제한사항 (Known Limitations)

1. **개발 환경**: API 키 없이 실행 가능 (프로덕션에서는 반드시 설정 필요)
2. **Rate Limiting**: 현재 구현되지 않음 (향후 추가 예정)
3. **IP 화이트리스트**: 현재 지원하지 않음

## 참고 자료 (References)

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [Docker Security Best Practices](https://docs.docker.com/develop/security-best-practices/)

## 업데이트 이력 (Changelog)

### 2026-01-09

- 초기 보안 정책 수립
- API 키 인증 시스템 구현
- Path Traversal 방어 강화
- Command Injection 방어 강화
- Docker 비특권 사용자 적용
- 보안 테스트 추가
