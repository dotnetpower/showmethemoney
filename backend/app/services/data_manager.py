"""데이터 관리 서비스 - GitHub repo를 DB로 사용"""
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import msgpack
from app.core.config import get_settings
from pydantic import BaseModel


class DataManager:
    """GitHub repo 파일 시스템을 통한 데이터 관리"""
    
    # 최대 파일 크기 (4MB)
    MAX_FILE_SIZE = 4 * 1024 * 1024
    
    def __init__(self):
        self.settings = get_settings()
        self.data_dir = self.settings.github_data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_provider_dir(self, provider_name: str) -> Path:
        """운용사별 데이터 디렉토리를 반환합니다."""
        provider_dir = self.data_dir / provider_name.lower()
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
        extension = "msgpack" if use_msgpack else "json"
        
        if chunk_index is not None:
            filename = f"{data_type}_part{chunk_index}.{extension}"
        else:
            filename = f"{data_type}.{extension}"
        
        return provider_dir / filename
    
    def _get_metadata_path(self, provider_name: str, data_type: str) -> Path:
        """메타데이터 파일 경로를 반환합니다."""
        provider_dir = self._get_provider_dir(provider_name)
        return provider_dir / f"{data_type}_metadata.json"
    
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
        data: Sequence[BaseModel],
        use_msgpack: bool = False
    ) -> Dict[str, Any]:
        """
        데이터를 저장합니다. 크기가 큰 경우 자동으로 분할합니다.
        
        Args:
            provider_name: 운용사 이름 (ishares, roundhill 등)
            data_type: 데이터 타입 (etf_list, dividend_info 등)
            data: 저장할 데이터 (Pydantic 모델 리스트)
            use_msgpack: MessagePack 사용 여부
            
        Returns:
            저장 정보 (파일 경로, 청크 개수 등)
        """
        # Pydantic 모델을 딕셔너리로 변환
        data_dicts = [item.model_dump(mode='json') for item in data]
        
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
        # 메타데이터 로드
        metadata_path = self._get_metadata_path(provider_name, data_type)
        if not metadata_path.exists():
            return []
        
        metadata = json.loads(metadata_path.read_text())
        use_msgpack = metadata.get("use_msgpack", False)
        
        # 분할된 데이터인 경우
        if metadata.get("chunked", False):
            all_data = []
            chunk_count = metadata["chunk_count"]
            
            for i in range(chunk_count):
                file_path = self._get_file_path(provider_name, data_type, use_msgpack, i)
                if file_path.exists():
                    chunk_data = self._deserialize_data(file_path.read_bytes(), use_msgpack)
                    all_data.extend(chunk_data)
            
            return all_data
        else:
            # 단일 파일인 경우
            file_path = self._get_file_path(provider_name, data_type, use_msgpack)
            if file_path.exists():
                return self._deserialize_data(file_path.read_bytes(), use_msgpack)
            return []
    
    async def get_metadata(self, provider_name: str, data_type: str) -> Optional[Dict]:
        """메타데이터를 반환합니다."""
        metadata_path = self._get_metadata_path(provider_name, data_type)
        if metadata_path.exists():
            return json.loads(metadata_path.read_text())
        return None
