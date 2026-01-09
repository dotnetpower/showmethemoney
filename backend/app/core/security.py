"""Security hooks for authentication/authorization."""

import os
from typing import Optional

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader

# API Key 헤더 (옵션: 프로덕션 환경에서 활성화)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def get_api_key() -> Optional[str]:
    """환경 변수에서 API 키 가져오기"""
    return os.getenv("API_KEY")


def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    API 키 검증
    
    환경 변수 API_KEY가 설정되어 있으면 API 키 검증을 활성화합니다.
    설정되어 있지 않으면 검증을 건너뜁니다 (개발 환경용).
    """
    required_api_key = get_api_key()
    
    # API 키가 환경 변수에 설정되지 않은 경우 검증 건너뛰기
    if not required_api_key:
        return "development"
    
    # API 키 검증
    if not api_key or api_key != required_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
    
    return api_key


def get_current_user(token: Optional[str] = None):
    """
    기본 토큰 체크 (레거시)
    
    참고: 프로덕션 환경에서는 verify_api_key 또는 OAuth2를 사용하세요.
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Missing token"
        )
    return {"token": token}
