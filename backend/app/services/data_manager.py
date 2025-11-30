"""데이터 관리 서비스 - GitHub repo를 DB로 사용"""
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import msgpack
from app.core.config import get_settings
from pydantic import BaseModel

# 모듈 레벨 로거 설정
logger = logging.getLogger(__name__)


class DataManager:
    """GitHub repo 파일 시스템을 통한 데이터 관리"""
    
    # 최대 파일 크기 (4MB)
    MAX_FILE_SIZE = 4 * 1024 * 1024
    
    # 허용된 문자 패턴 (영문자/숫자로 시작, 이후 영문, 숫자, 하이픈, 언더스코어, 공백 허용)
    SAFE_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9_ -]*$')
    
    def __init__(self):
        logger.info("[DataManager] Initializing DataManager")
        self.settings = get_settings()
        self.data_dir = self.settings.github_data_dir
        
        logger.info(f"[DataManager] Data directory: {self.data_dir}")
        logger.info(f"[DataManager] Data directory exists: {self.data_dir.exists()}")
        
        # 디렉토리가 없으면 생성
        if not self.data_dir.exists():
            logger.warning(f"[DataManager] Data directory does not exist, creating: {self.data_dir}")
            try:
                self.data_dir.mkdir(parents=True, exist_ok=True)
                logger.info(f"[DataManager] Created data directory: {self.data_dir}")
            except Exception as e:
                logger.error(f"[DataManager] Failed to create data directory: {e}")
                raise
        else:
            # 디렉토리 내용 로깅
            try:
                items = list(self.data_dir.iterdir())
                subdirs = [item for item in items if item.is_dir()]
                files = [item for item in items if item.is_file()]
                logger.info(f"[DataManager] Data directory has {len(subdirs)} subdirs, {len(files)} files")
                logger.info(f"[DataManager] Subdirectories: {[d.name for d in subdirs[:10]]}")
                if len(subdirs) > 10:
                    logger.info(f"[DataManager]   ... and {len(subdirs) - 10} more subdirs")
            except Exception as e:
                logger.error(f"[DataManager] Error listing data directory: {e}")
    
    def _sanitize_name(self, name: str) -> str:
        """
        이름을 검증하고 안전한 형태로 반환합니다.
        Path Traversal 공격을 방지합니다.
        
        Args:
            name: 검증할 이름
            
        Returns:
            안전한 이름
            
        Raises:
            ValueError: 유효하지 않은 이름인 경우
        """
        if not name:
            raise ValueError("Name cannot be empty")
        
        # 위험한 문자 제거 및 검증
        sanitized = name.strip().lower()
        
        # Path traversal 시도 방지
        if '..' in sanitized or '/' in sanitized or '\\' in sanitized:
            raise ValueError("Invalid name: contains path traversal characters")
        
        # 허용된 문자만 사용하는지 확인
        if not self.SAFE_NAME_PATTERN.match(sanitized):
            raise ValueError("Invalid name: contains disallowed characters")
        
        return sanitized
    
    def _get_provider_dir(self, provider_name: str) -> Path:
        """운용사별 데이터 디렉토리를 반환합니다."""
        # 입력 검증
        safe_name = self._sanitize_name(provider_name)
        provider_dir = self.data_dir / safe_name
        
        # 경로가 data_dir 내에 있는지 확인 (추가 보안 검증)
        try:
            provider_dir.resolve().relative_to(self.data_dir.resolve())
        except ValueError:
            raise ValueError("Invalid provider name: path traversal detected")
        
        provider_dir.mkdir(parents=True, exist_ok=True)
        return provider_dir
    
    def _get_file_path(
        self, 
        provider_name: str, 
        data_type: str, 
        use_msgpack: bool = False,
        chunk_index: Optional[int] = None
    ) -> Path:
        """데이터 파일 경로를 반환합니다."""
        provider_dir = self._get_provider_dir(provider_name)
        # data_type 검증
        safe_data_type = self._sanitize_name(data_type)
        extension = "msgpack" if use_msgpack else "json"
        
        if chunk_index is not None:
            # chunk_index가 음수가 아닌 정수인지 확인
            if not isinstance(chunk_index, int) or chunk_index < 0:
                raise ValueError("chunk_index must be a non-negative integer")
            filename = f"{safe_data_type}_part{chunk_index}.{extension}"
        else:
            filename = f"{safe_data_type}.{extension}"
        
        return provider_dir / filename
    
    def _get_metadata_path(self, provider_name: str, data_type: str) -> Path:
        """메타데이터 파일 경로를 반환합니다."""
        provider_dir = self._get_provider_dir(provider_name)
        # data_type 검증
        safe_data_type = self._sanitize_name(data_type)
        return provider_dir / f"{safe_data_type}_metadata.json"
    
    def _serialize_data(self, data: Any, use_msgpack: bool = False) -> bytes:
        """데이터를 직렬화합니다."""
        if use_msgpack:
            result: bytes = msgpack.packb(data, use_bin_type=True)  # type: ignore
            return result
        else:
            return json.dumps(data, indent=2, ensure_ascii=False, default=str).encode('utf-8')
    
    def _deserialize_data(self, data: bytes, use_msgpack: bool = False) -> Any:
        """데이터를 역직렬화합니다."""
        if use_msgpack:
            return msgpack.unpackb(data, raw=False)
        else:
            return json.loads(data.decode('utf-8'))
    
    def _split_data(self, data: List[Dict], max_size: int) -> List[List[Dict]]:
        """데이터를 최대 크기에 맞게 분할합니다."""
        chunks = []
        current_chunk = []
        current_size = 0
        
        for item in data:
            item_size = len(json.dumps(item, default=str).encode('utf-8'))
            
            if current_size + item_size > max_size and current_chunk:
                chunks.append(current_chunk)
                current_chunk = [item]
                current_size = item_size
            else:
                current_chunk.append(item)
                current_size += item_size
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    async def save_data(
        self,
        provider_name: str,
        data_type: str,
        data: Sequence[BaseModel | Dict[str, Any]],
        use_msgpack: bool = False
    ) -> Dict[str, Any]:
        """
        데이터를 저장합니다. 크기가 큰 경우 자동으로 분할합니다.
        
        Args:
            provider_name: 운용사 이름 (ishares, roundhill 등)
            data_type: 데이터 타입 (etf_list, dividend_info 등)
            data: 저장할 데이터 (Pydantic 모델 리스트 또는 딕셔너리 리스트)
            use_msgpack: MessagePack 사용 여부
            
        Returns:
            저장 정보 (파일 경로, 청크 개수 등)
        """
        # Pydantic 모델 또는 딕셔너리를 딕셔너리로 변환
        data_dicts = []
        for item in data:
            if isinstance(item, BaseModel):
                data_dicts.append(item.model_dump(mode='json'))
            elif isinstance(item, dict):
                data_dicts.append(item)
            else:
                raise ValueError(f"Unsupported data type: {type(item)}")
        
        # 전체 데이터 크기 확인
        serialized = self._serialize_data(data_dicts, use_msgpack)
        total_size = len(serialized)
        
        metadata = {
            "provider": provider_name,
            "data_type": data_type,
            "updated_at": datetime.now().isoformat(),
            "total_count": len(data_dicts),
            "total_size": total_size,
            "use_msgpack": use_msgpack,
        }
        
        # 크기가 제한을 초과하면 분할
        if total_size > self.MAX_FILE_SIZE:
            chunks = self._split_data(data_dicts, self.MAX_FILE_SIZE)
            metadata["chunked"] = True
            metadata["chunk_count"] = len(chunks)
            
            # 각 청크 저장
            for i, chunk in enumerate(chunks):
                file_path = self._get_file_path(provider_name, data_type, use_msgpack, i)
                chunk_data = self._serialize_data(chunk, use_msgpack)
                file_path.write_bytes(chunk_data)
                
                metadata[f"chunk_{i}"] = {
                    "file": file_path.name,
                    "count": len(chunk),
                    "size": len(chunk_data)
                }
        else:
            # 단일 파일로 저장
            file_path = self._get_file_path(provider_name, data_type, use_msgpack)
            file_path.write_bytes(serialized)
            
            metadata["chunked"] = False
            metadata["file"] = file_path.name
        
        # 메타데이터 저장
        metadata_path = self._get_metadata_path(provider_name, data_type)
        metadata_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False))
        
        return metadata
    
    async def load_data(
        self,
        provider_name: str,
        data_type: str
    ) -> List[Dict]:
        """
        저장된 데이터를 로드합니다.
        
        Args:
            provider_name: 운용사 이름
            data_type: 데이터 타입
            
        Returns:
            데이터 리스트
        """
        logger.debug(f"[DataManager] Loading data for provider={provider_name}, data_type={data_type}")
        
        # 메타데이터 로드
        metadata_path = self._get_metadata_path(provider_name, data_type)
        logger.debug(f"[DataManager] Metadata path: {metadata_path}")
        logger.debug(f"[DataManager] Metadata path exists: {metadata_path.exists()}")
        
        if not metadata_path.exists():
            logger.debug(f"[DataManager] Metadata not found for {provider_name}/{data_type}")
            # 프로바이더 디렉토리 존재 여부 확인
            provider_dir = self.data_dir / self._sanitize_name(provider_name)
            logger.debug(f"[DataManager] Provider dir: {provider_dir}, exists: {provider_dir.exists()}")
            if provider_dir.exists():
                try:
                    contents = list(provider_dir.iterdir())
                    logger.debug(f"[DataManager] Provider dir contents: {[f.name for f in contents]}")
                except Exception as e:
                    logger.error(f"[DataManager] Error listing provider dir: {e}")
            return []
        
        try:
            metadata = json.loads(metadata_path.read_text())
            use_msgpack = metadata.get("use_msgpack", False)
            logger.debug(f"[DataManager] Loaded metadata: chunked={metadata.get('chunked')}, total_count={metadata.get('total_count')}")
            
            # 분할된 데이터인 경우
            if metadata.get("chunked", False):
                all_data = []
                chunk_count = metadata["chunk_count"]
                logger.debug(f"[DataManager] Loading {chunk_count} chunks")
                
                for i in range(chunk_count):
                    file_path = self._get_file_path(provider_name, data_type, use_msgpack, i)
                    file_exists = file_path.exists()
                    logger.debug(f"[DataManager] Chunk {i} path: {file_path}, exists: {file_exists}")
                    if file_exists:
                        chunk_data = self._deserialize_data(file_path.read_bytes(), use_msgpack)
                        all_data.extend(chunk_data)
                        logger.debug(f"[DataManager] Loaded chunk {i} with {len(chunk_data)} items")
                
                logger.info(f"[DataManager] Loaded total {len(all_data)} items for {provider_name}/{data_type}")
                return all_data
            else:
                # 단일 파일인 경우
                file_path = self._get_file_path(provider_name, data_type, use_msgpack)
                file_exists = file_path.exists()
                logger.debug(f"[DataManager] Single file path: {file_path}, exists: {file_exists}")
                if file_exists:
                    data = self._deserialize_data(file_path.read_bytes(), use_msgpack)
                    logger.info(f"[DataManager] Loaded {len(data)} items for {provider_name}/{data_type}")
                    return data
                else:
                    logger.warning(f"[DataManager] Data file not found: {file_path}")
                return []
        except Exception as e:
            logger.error(f"[DataManager] Error loading data for {provider_name}/{data_type}: {e}", exc_info=True)
            return []
    
    async def get_metadata(self, provider_name: str, data_type: str) -> Optional[Dict]:
        """메타데이터를 반환합니다."""
        metadata_path = self._get_metadata_path(provider_name, data_type)
        if metadata_path.exists():
            return json.loads(metadata_path.read_text())
        return None
