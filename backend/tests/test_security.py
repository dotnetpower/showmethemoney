"""보안 관련 테스트"""
import pytest
import os
from unittest.mock import patch

from app.services.data_manager import DataManager


class TestDataManagerSecurity:
    """DataManager의 보안 기능 테스트"""
    
    def test_sanitize_name_valid(self):
        """유효한 이름은 정상 처리되어야 함"""
        dm = DataManager()
        
        assert dm._sanitize_name("ishares") == "ishares"
        assert dm._sanitize_name("Alpha_Architect") == "alpha_architect"
        assert dm._sanitize_name("First-Trust") == "first-trust"
        assert dm._sanitize_name("Test123") == "test123"
        assert dm._sanitize_name("a") == "a"  # 최소 1문자
    
    def test_sanitize_name_starting_with_special_char(self):
        """하이픈이나 언더스코어로 시작하는 이름은 차단되어야 함"""
        dm = DataManager()
        
        with pytest.raises(ValueError, match="disallowed characters"):
            dm._sanitize_name("-ishares")
        
        with pytest.raises(ValueError, match="disallowed characters"):
            dm._sanitize_name("_ishares")
    
    def test_sanitize_name_empty(self):
        """빈 이름은 ValueError를 발생시켜야 함"""
        dm = DataManager()
        
        with pytest.raises(ValueError, match="cannot be empty"):
            dm._sanitize_name("")
    
    def test_sanitize_name_path_traversal(self):
        """Path traversal 시도는 차단되어야 함"""
        dm = DataManager()
        
        # ..를 포함한 경로 시도
        with pytest.raises(ValueError, match="path traversal"):
            dm._sanitize_name("../etc/passwd")
        
        with pytest.raises(ValueError, match="path traversal"):
            dm._sanitize_name("..\\windows\\system32")
        
        # 슬래시가 포함된 경로 시도
        with pytest.raises(ValueError, match="path traversal"):
            dm._sanitize_name("provider/subdir")
        
        with pytest.raises(ValueError, match="path traversal"):
            dm._sanitize_name("provider\\subdir")
    
    def test_sanitize_name_special_characters(self):
        """특수 문자가 포함된 이름은 차단되어야 함"""
        dm = DataManager()
        
        with pytest.raises(ValueError, match="disallowed characters"):
            dm._sanitize_name("provider@example")
        
        with pytest.raises(ValueError, match="disallowed characters"):
            dm._sanitize_name("provider$")
        
        with pytest.raises(ValueError, match="disallowed characters"):
            dm._sanitize_name("provider%20name")
        
        with pytest.raises(ValueError, match="disallowed characters"):
            dm._sanitize_name("provider<script>")
    
    def test_get_provider_dir_validates_input(self):
        """_get_provider_dir은 입력을 검증해야 함"""
        dm = DataManager()
        
        with pytest.raises(ValueError):
            dm._get_provider_dir("../malicious")
        
        with pytest.raises(ValueError):
            dm._get_provider_dir("")
    
    def test_get_file_path_validates_data_type(self):
        """_get_file_path는 data_type을 검증해야 함"""
        dm = DataManager()
        
        with pytest.raises(ValueError):
            dm._get_file_path("ishares", "../malicious")
        
        with pytest.raises(ValueError):
            dm._get_file_path("ishares", "")
    
    def test_get_file_path_validates_chunk_index(self):
        """_get_file_path는 chunk_index를 검증해야 함"""
        dm = DataManager()
        
        # 음수 chunk_index는 차단되어야 함
        with pytest.raises(ValueError, match="non-negative integer"):
            dm._get_file_path("ishares", "etf_list", chunk_index=-1)
        
        # 유효한 chunk_index는 정상 처리
        path = dm._get_file_path("ishares", "etf_list", chunk_index=0)
        assert "part0" in str(path)


class TestETFApiSecurity:
    """ETF API의 보안 기능 테스트"""
    
    def test_validate_provider_name_valid(self):
        """유효한 provider 이름은 정상 처리되어야 함"""
        from app.api.v1.etf import validate_provider_name
        
        assert validate_provider_name("ishares") == "ishares"
        assert validate_provider_name("Alpha Architect") == "Alpha Architect"
        assert validate_provider_name("First-Trust") == "First-Trust"
    
    def test_validate_provider_name_empty(self):
        """빈 이름은 HTTPException을 발생시켜야 함"""
        from app.api.v1.etf import validate_provider_name
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc_info:
            validate_provider_name("")
        
        assert exc_info.value.status_code == 400
    
    def test_validate_provider_name_too_long(self):
        """너무 긴 이름은 HTTPException을 발생시켜야 함"""
        from app.api.v1.etf import validate_provider_name
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc_info:
            validate_provider_name("a" * 101)
        
        assert exc_info.value.status_code == 400
    
    def test_validate_provider_name_special_characters(self):
        """특수 문자가 포함된 이름은 HTTPException을 발생시켜야 함"""
        from app.api.v1.etf import validate_provider_name
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc_info:
            validate_provider_name("provider<script>alert('xss')</script>")
        
        assert exc_info.value.status_code == 400
        
        with pytest.raises(HTTPException) as exc_info:
            validate_provider_name("../etc/passwd")
        
        assert exc_info.value.status_code == 400


class TestSecurityConfiguration:
    """보안 설정 테스트"""
    
    def test_api_key_validation_with_key(self):
        """API 키가 설정된 경우 검증이 작동해야 함"""
        from app.core.security import verify_api_key
        from fastapi import HTTPException
        
        with patch.dict(os.environ, {"API_KEY": "test-api-key"}):
            # 올바른 키
            assert verify_api_key("test-api-key") == "test-api-key"
            
            # 잘못된 키
            with pytest.raises(HTTPException) as exc_info:
                verify_api_key("wrong-key")
            assert exc_info.value.status_code == 401
            
            # 키 없음
            with pytest.raises(HTTPException) as exc_info:
                verify_api_key(None)
            assert exc_info.value.status_code == 401
    
    def test_api_key_validation_without_key(self):
        """API 키가 설정되지 않은 경우 검증을 건너뛰어야 함"""
        from app.core.security import verify_api_key
        
        with patch.dict(os.environ, {}, clear=True):
            # 키가 없어도 통과
            assert verify_api_key(None) == "development"
            assert verify_api_key("any-key") == "development"


class TestAgentSecurity:
    """Agent 보안 테스트"""
    
    def test_base_agent_requires_api_key(self):
        """BaseAgent는 OpenAI API 키를 요구해야 함"""
        from app.agents.base_agent import BaseAgent
        
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="OpenAI API key is required"):
                BaseAgent(
                    name="test",
                    instructions="test",
                    config={}
                )
    
    def test_base_agent_accepts_api_key_from_env(self):
        """BaseAgent는 환경 변수에서 API 키를 가져와야 함"""
        from app.agents.base_agent import BaseAgent
        
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            agent = BaseAgent(
                name="test",
                instructions="test",
                config={}
            )
            # config에서 먼저 확인하고, 없으면 환경 변수에서 확인
            api_key = agent.config.get("openai_api_key") or os.getenv("OPENAI_API_KEY")
            assert api_key == "test-key"
    
    def test_base_agent_accepts_api_key_from_config(self):
        """BaseAgent는 config에서 API 키를 가져와야 함"""
        from app.agents.base_agent import BaseAgent
        
        with patch.dict(os.environ, {}, clear=True):
            agent = BaseAgent(
                name="test",
                instructions="test",
                config={"openai_api_key": "config-key"}
            )
            assert agent.config.get("openai_api_key") == "config-key"


class TestCommandInjection:
    """명령어 주입 취약점 테스트"""
    
    def test_git_commit_push_validates_file_path(self):
        """git_commit_push는 파일 경로를 검증해야 함"""
        from app.agents.data_storage_agent import git_commit_push
        
        # 절대 경로 차단
        result = git_commit_push("/etc/passwd", "test")
        assert "Invalid file path" in result or "유효하지 않은" in result
        
        # Path traversal 차단
        result = git_commit_push("../../../etc/passwd", "test")
        assert "Invalid file path" in result or "path traversal" in result or "유효하지 않은" in result
    
    def test_git_commit_push_validates_commit_message(self):
        """git_commit_push는 커밋 메시지 길이를 제한해야 함"""
        from app.agents.data_storage_agent import git_commit_push
        
        # 너무 긴 메시지
        long_message = "a" * 501
        result = git_commit_push("test.json", long_message)
        assert "too long" in result or "유효하지 않은" in result
