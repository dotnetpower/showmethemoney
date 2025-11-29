"""보안 관련 테스트"""
import pytest

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
