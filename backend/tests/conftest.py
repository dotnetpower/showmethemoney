"""pytest 설정 파일"""
import sys
from pathlib import Path

# backend 디렉토리를 Python path에 추가
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))
