"""
Data Storage Agent
데이터를 GitHub Repository에 저장 및 관리하는 Agent
Microsoft Agent Framework 기반
"""

import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Annotated, Any, Dict, List, Optional

from pydantic import Field

from .base_agent import BaseAgent


def save_json_file(
    file_path: Annotated[str, Field(description="저장할 파일 경로")],
    data: Annotated[Any, Field(description="저장할 JSON 데이터")]
) -> str:
    """JSON 데이터를 파일에 저장"""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return f"파일 저장 완료: {file_path}"


def load_json_file(
    file_path: Annotated[str, Field(description="로드할 파일 경로")]
) -> Dict[str, Any]:
    """JSON 파일 로드"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data


def delete_file(
    file_path: Annotated[str, Field(description="삭제할 파일 경로")]
) -> str:
    """파일 삭제"""
    path = Path(file_path)
    if path.exists():
        path.unlink()
        return f"파일 삭제 완료: {file_path}"
    return f"파일이 존재하지 않음: {file_path}"


def git_commit_push(
    file_path: Annotated[str, Field(description="커밋할 파일 경로")],
    commit_message: Annotated[str, Field(description="커밋 메시지")]
) -> str:
    """Git commit 및 push"""
    try:
        subprocess.run(["git", "add", file_path], check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", commit_message], check=True, capture_output=True)
        subprocess.run(["git", "push"], check=True, capture_output=True)
        return f"Git push 완료: {file_path}"
    except subprocess.CalledProcessError as e:
        return f"Git 작업 실패: {str(e)}"


class DataStorageAgent(BaseAgent):
    """데이터 저장 Agent (GitHub Repo as DB)"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        config = config or {}
        
        instructions = """
        당신은 GitHub Repository를 데이터베이스로 활용하는 스토리지 전문 Agent입니다.
        
        주요 역할:
        1. 데이터를 JSON 파일로 GitHub repository에 저장
        2. 저장된 데이터 조회 및 로드
        3. 데이터 삭제
        4. Git commit 및 push를 통한 데이터 버전 관리
        
        작업 시 주의사항:
        - 파일 크기는 4MB 이하로 제한
        - 대용량 데이터는 여러 파일로 분할 저장
        - 메타데이터 파일을 함께 생성하여 관리
        - Git branch를 활용한 안전한 데이터 변경
        """
        
        tools = [save_json_file, load_json_file, delete_file, git_commit_push]
        
        super().__init__(
            name="DataStorage",
            instructions=instructions,
            tools=tools,
            config=config
        )
        
        self.data_dir = Path(config.get("data_dir", "data"))
        self.max_file_size = config.get("max_file_size", 4 * 1024 * 1024)  # 4MB
        self.use_branches = config.get("use_branches", True)
    
    async def execute(self, operation: str, **kwargs) -> Dict[str, Any]:
        """
        스토리지 작업 실행
        
        Args:
            operation: 작업 타입 (save, load, delete)
            **kwargs: 작업별 파라미터
            
        Returns:
            작업 결과
        """
        try:
            self.log_info(f"스토리지 작업 시작: {operation}")
            
            if not await self.validate(operation=operation, **kwargs):
                raise ValueError("유효하지 않은 작업")
            
            if operation == "save":
                result = await self.save(**kwargs)
            elif operation == "load":
                result = await self.load(**kwargs)
            elif operation == "delete":
                result = await self.delete(**kwargs)
            else:
                raise ValueError(f"지원하지 않는 작업: {operation}")
            
            self.log_info(f"스토리지 작업 완료: {operation}")
            return result
            
        except Exception as e:
            self.log_error(f"스토리지 작업 실패: {operation}", exc_info=e)
            return {
                "operation": operation,
                "status": "error",
                "error": str(e)
            }
    
    async def validate(self, operation: str, **kwargs) -> bool:
        """
        작업 검증
        
        Args:
            operation: 작업 타입
            **kwargs: 작업 파라미터
            
        Returns:
            유효성 여부
        """
        valid_operations = ["save", "load", "delete"]
        if operation not in valid_operations:
            return False
        
        if operation == "save":
            if "data" not in kwargs or "path" not in kwargs:
                return False
        elif operation in ["load", "delete"]:
            if "path" not in kwargs:
                return False
        
        return True
        
    async def save(
        self, 
        data: Any, 
        path: str, 
        branch: Optional[str] = None,
        commit_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        데이터 저장
        
        Args:
            data: 저장할 데이터
            path: 저장 경로 (상대 경로)
            branch: 사용할 브랜치명
            commit_message: 커밋 메시지
            
        Returns:
            저장 결과
        """
        try:
            self.log_info(f"데이터 저장 시작: {path}")
            
            file_path = self.data_dir / path
            
            # 데이터 크기 체크
            data_str = json.dumps(data, ensure_ascii=False)
            data_size = len(data_str.encode('utf-8'))
            
            if data_size > self.max_file_size:
                self.log_warning(f"대용량 데이터 감지: {data_size} bytes")
                return await self._save_large_data(data, path, branch, commit_message)
            
            task = f"""
            다음 데이터를 {file_path}에 JSON 파일로 저장해주세요:
            
            {data_str[:1000]}... (총 {data_size} bytes)
            
            작업 순서:
            1. save_json_file 함수를 사용하여 데이터 저장
            2. 메타데이터 파일 생성 (경로, 크기, 타임스탬프 포함)
            {f"3. git_commit_push 함수로 커밋 및 푸시 (메시지: {commit_message or 'Update data'})" if self.use_branches else ""}
            """
            
            result = await self.run(task)
            
            return {
                "operation": "save",
                "path": str(file_path),
                "size": data_size,
                "status": "success",
                "result": str(result)
            }
            
        except Exception as e:
            self.log_error(f"데이터 저장 실패: {path}", exc_info=e)
            return {
                "operation": "save",
                "status": "error",
                "error": str(e)
            }
    
    async def load(self, path: str) -> Dict[str, Any]:
        """
        데이터 로드
        
        Args:
            path: 로드할 파일 경로
            
        Returns:
            로드된 데이터
        """
        try:
            self.log_info(f"데이터 로드 시작: {path}")
            
            file_path = self.data_dir / path
            
            task = f"""
            {file_path}에서 JSON 데이터를 로드해주세요.
            
            작업 순서:
            1. 먼저 메타데이터 파일 확인 (chunked 타입인지 확인)
            2. load_json_file 함수로 데이터 로드
            3. chunked 타입이면 모든 청크 파일 로드 및 병합
            
            로드된 데이터를 반환해주세요.
            """
            
            result = await self.run(task)
            
            return {
                "operation": "load",
                "path": str(path),
                "data": result,
                "status": "success"
            }
            
        except Exception as e:
            self.log_error(f"데이터 로드 실패: {path}", exc_info=e)
            return {
                "operation": "load",
                "data": None,
                "status": "error",
                "error": str(e)
            }
    
    async def delete(self, path: str, commit_message: Optional[str] = None) -> Dict[str, Any]:
        """
        데이터 삭제
        
        Args:
            path: 삭제할 파일 경로
            commit_message: 커밋 메시지
            
        Returns:
            삭제 결과
        """
        try:
            self.log_info(f"데이터 삭제 시작: {path}")
            
            file_path = self.data_dir / path
            
            task = f"""
            {file_path} 파일을 삭제해주세요.
            
            작업 순서:
            1. delete_file 함수로 파일 삭제
            2. 메타데이터 파일도 삭제
            {f"3. git_commit_push 함수로 커밋 및 푸시 (메시지: {commit_message or 'Delete data'})" if self.use_branches else ""}
            """
            
            result = await self.run(task)
            
            return {
                "operation": "delete",
                "path": str(path),
                "status": "success",
                "result": str(result)
            }
            
        except Exception as e:
            self.log_error(f"데이터 삭제 실패: {path}", exc_info=e)
            return {
                "operation": "delete",
                "status": "error",
                "error": str(e)
            }
    
    async def _save_large_data(
        self, 
        data: List[Any], 
        path: str, 
        branch: Optional[str] = None,
        commit_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        대용량 데이터 분할 저장
        
        Args:
            data: 저장할 데이터 (리스트)
            path: 저장 경로
            branch: 브랜치명
            commit_message: 커밋 메시지
            
        Returns:
            저장 결과
        """
        if not isinstance(data, list):
            raise ValueError("대용량 데이터는 리스트 형태여야 합니다")
        
        file_path = self.data_dir / path
        
        # 청크 크기 계산
        chunk_size = len(data) // ((len(json.dumps(data).encode('utf-8')) // self.max_file_size) + 1)
        
        chunks_info = []
        for i in range(0, len(data), chunk_size):
            chunk = data[i:i + chunk_size]
            chunk_path = file_path.parent / f"{file_path.stem}_part{i//chunk_size + 1}.json"
            
            # 각 청크 저장
            save_json_file(str(chunk_path), chunk)
            
            chunks_info.append({
                "path": str(chunk_path.relative_to(self.data_dir)),
                "size": len(json.dumps(chunk).encode('utf-8')),
                "items": len(chunk)
            })
        
        # 분할 정보 메타데이터 저장
        metadata = {
            "path": str(path),
            "type": "chunked",
            "total_chunks": len(chunks_info),
            "chunks": chunks_info,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        metadata_path = file_path.parent / f"{file_path.stem}_metadata.json"
        save_json_file(str(metadata_path), metadata)
        
        self.log_info(f"대용량 데이터 분할 저장 완료: {len(chunks_info)} 청크")
        
        return {
            "operation": "save",
            "path": str(path),
            "type": "chunked",
            "chunks": len(chunks_info),
            "status": "success"
        }
