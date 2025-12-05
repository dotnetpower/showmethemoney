"""
Data Processing Agent
수집된 데이터를 정제 및 변환하는 Agent
Microsoft Agent Framework 기반
"""

import json
from datetime import datetime
from typing import Annotated, Any, Dict, List, Optional

import msgpack
from pydantic import Field

from .base_agent import BaseAgent


def clean_data_item(item: Annotated[Dict[str, Any], Field(description="정제할 데이터 아이템")]) -> Dict[str, Any]:
    """개별 데이터 아이템 정제"""
    if not isinstance(item, dict):
        return item
    
    # null, empty string 제거
    cleaned = {
        k: v for k, v in item.items() 
        if v is not None and v != "" and v != []
    }
    return cleaned


def validate_data_structure(data: Annotated[Any, Field(description="검증할 데이터")]) -> Dict[str, Any]:
    """데이터 구조 유효성 검사"""
    validation_result = {
        "is_valid": True,
        "errors": [],
        "warnings": []
    }
    
    if isinstance(data, list):
        for idx, item in enumerate(data):
            if not isinstance(item, dict):
                validation_result["warnings"].append(
                    f"Index {idx}: 딕셔너리가 아닌 항목"
                )
            elif "ticker" not in item:
                validation_result["errors"].append(
                    f"Index {idx}: ticker 필드 누락"
                )
                validation_result["is_valid"] = False
    
    return validation_result


def remove_duplicates(
    data: Annotated[List[Dict[str, Any]], Field(description="중복 제거할 데이터")],
    key: Annotated[str, Field(description="중복 체크 기준 키")] = "ticker"
) -> List[Dict[str, Any]]:
    """중복 데이터 제거"""
    if not isinstance(data, list):
        return data
    
    seen = set()
    unique_data = []
    
    for item in data:
        if not isinstance(item, dict):
            unique_data.append(item)
            continue
        
        item_key = item.get(key, str(item))
        if item_key not in seen:
            seen.add(item_key)
            unique_data.append(item)
    
    return unique_data


class DataProcessingAgent(BaseAgent):
    """데이터 처리 Agent"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        config = config or {}
        
        instructions = """
        당신은 데이터를 정제하고 변환하는 전문 Agent입니다.
        
        주요 역할:
        1. 수집된 데이터의 중복 제거
        2. null 값 및 빈 문자열 제거
        3. 데이터 형식 변환 (JSON, MessagePack)
        4. 데이터 유효성 검사
        
        데이터 처리 시:
        - 제공된 도구를 활용하여 데이터 정제
        - 유효성 검사 수행
        - 필요한 형식으로 변환
        - 처리 결과를 명확하게 반환
        """
        
        tools = [clean_data_item, validate_data_structure, remove_duplicates]
        
        super().__init__(
            name="DataProcessing",
            instructions=instructions,
            tools=tools,
            config=config
        )
        
        self.use_msgpack = config.get("use_msgpack", False)
    
    async def execute(self, operation: str, data: Any = None, **kwargs) -> Dict[str, Any]:
        """
        데이터 처리 작업 실행
        
        Args:
            operation: 작업 타입 (clean, transform, validate, deduplicate)
            data: 처리할 데이터
            **kwargs: 작업별 파라미터
            
        Returns:
            작업 결과
        """
        try:
            self.log_info(f"데이터 처리 작업 시작: {operation}")
            
            if not await self.validate_operation(operation=operation, data=data, **kwargs):
                raise ValueError("유효하지 않은 작업")
            
            if operation == "clean":
                result = await self.clean(data)
            elif operation == "transform":
                format_type = kwargs.get("format_type", "json")
                result = await self.transform(data, format_type)
            elif operation == "validate":
                result = await self.validate(data)
            elif operation == "deduplicate":
                key = kwargs.get("key", "ticker")
                result = await self.deduplicate(data, key)
            else:
                raise ValueError(f"지원하지 않는 작업: {operation}")
            
            self.log_info(f"데이터 처리 작업 완료: {operation}")
            return result
            
        except Exception as e:
            self.log_error(f"데이터 처리 작업 실패: {operation}", exc_info=e)
            return {
                "operation": operation,
                "status": "error",
                "error": str(e)
            }
    
    async def validate_operation(self, operation: str, data: Any = None, **kwargs) -> bool:
        """
        작업 검증
        
        Args:
            operation: 작업 타입
            data: 데이터
            **kwargs: 작업 파라미터
            
        Returns:
            유효성 여부
        """
        valid_operations = ["clean", "transform", "validate", "deduplicate"]
        if operation not in valid_operations:
            return False
        
        if data is None:
            return False
        
        return True
        
    async def clean(self, data: Any) -> Dict[str, Any]:
        """
        데이터 정제
        
        Args:
            data: 정제할 데이터
            
        Returns:
            정제된 데이터
        """
        try:
            self.log_info("데이터 정제 시작")
            
            task = f"""
            다음 데이터를 정제해주세요:
            
            {json.dumps(data, ensure_ascii=False, indent=2)}
            
            작업 내용:
            1. null 값 및 빈 문자열 제거
            2. 불필요한 필드 제거
            3. 데이터 타입 정규화
            
            결과를 JSON 형태로 반환해주세요.
            """
            
            result = await self.run(task)
            
            return {
                "operation": "clean",
                "data": result,
                "timestamp": datetime.utcnow().isoformat(),
                "status": "success"
            }
            
        except Exception as e:
            self.log_error("데이터 정제 실패", exc_info=e)
            return {
                "operation": "clean",
                "data": None,
                "timestamp": datetime.utcnow().isoformat(),
                "status": "error",
                "error": str(e)
            }
    
    async def transform(self, data: Any, format_type: str = "json") -> Dict[str, Any]:
        """
        데이터 형식 변환
        
        Args:
            data: 변환할 데이터
            format_type: 대상 형식 (json, msgpack)
            
        Returns:
            변환된 데이터
        """
        try:
            self.log_info(f"데이터 변환 시작: {format_type}")
            
            if format_type == "json":
                transformed = json.dumps(data, ensure_ascii=False, indent=2)
            elif format_type == "msgpack":
                transformed = msgpack.packb(data, use_bin_type=True)  # type: ignore
            else:
                raise ValueError(f"지원하지 않는 형식: {format_type}")
            
            return {
                "operation": "transform",
                "format": format_type,
                "data": transformed,
                "timestamp": datetime.utcnow().isoformat(),
                "status": "success"
            }
            
        except Exception as e:
            self.log_error(f"데이터 변환 실패: {format_type}", exc_info=e)
            return {
                "operation": "transform",
                "data": None,
                "timestamp": datetime.utcnow().isoformat(),
                "status": "error",
                "error": str(e)
            }
    
    async def validate(self, data: Any) -> Dict[str, Any]:
        """
        데이터 유효성 검사
        
        Args:
            data: 검사할 데이터
            
        Returns:
            검증 결과
        """
        try:
            self.log_info("데이터 유효성 검사 시작")
            
            task = f"""
            다음 데이터의 유효성을 검사해주세요:
            
            {json.dumps(data, ensure_ascii=False, indent=2)}
            
            검사 항목:
            1. 필수 필드 존재 여부 (ticker, name 등)
            2. 데이터 타입 적합성
            3. 데이터 일관성
            
            검증 결과를 다음 형태로 반환:
            {{
                "is_valid": true/false,
                "errors": [],
                "warnings": []
            }}
            """
            
            result = await self.run(task)
            
            return {
                "operation": "validate",
                "validation_result": result,
                "timestamp": datetime.utcnow().isoformat(),
                "status": "success"
            }
            
        except Exception as e:
            self.log_error("데이터 유효성 검사 실패", exc_info=e)
            return {
                "operation": "validate",
                "validation_result": None,
                "timestamp": datetime.utcnow().isoformat(),
                "status": "error",
                "error": str(e)
            }
    
    async def deduplicate(self, data: List[Dict[str, Any]], key: str = "ticker") -> Dict[str, Any]:
        """
        중복 데이터 제거
        
        Args:
            data: 중복 제거할 데이터 리스트
            key: 중복 체크 기준 키
            
        Returns:
            중복이 제거된 데이터
        """
        try:
            self.log_info("중복 제거 시작")
            
            unique_data = remove_duplicates(data, key)
            
            self.log_info(f"중복 제거 완료: {len(data)} -> {len(unique_data)}")
            
            return {
                "operation": "deduplicate",
                "data": unique_data,
                "original_count": len(data),
                "unique_count": len(unique_data),
                "timestamp": datetime.utcnow().isoformat(),
                "status": "success"
            }
            
        except Exception as e:
            self.log_error("중복 제거 실패", exc_info=e)
            return {
                "operation": "deduplicate",
                "data": None,
                "timestamp": datetime.utcnow().isoformat(),
                "status": "error",
                "error": str(e)
            }
    
    async def compress_data(self, data: Any) -> bytes:
        """
        데이터 압축 (MessagePack)
        
        Args:
            data: 압축할 데이터
            
        Returns:
            압축된 바이너리 데이터
        """
        return msgpack.packb(data, use_bin_type=True)  # type: ignore
    
    async def decompress_data(self, compressed_data: bytes) -> Any:
        """
        데이터 압축 해제
        
        Args:
            compressed_data: 압축된 데이터
            
        Returns:
            압축 해제된 데이터
        """
        return msgpack.unpackb(compressed_data, raw=False)
