"""
Base Agent 클래스
Microsoft Agent Framework 기반의 Agent 구조
"""

import logging
from typing import Any, Callable, Dict, List, Optional

from agent_framework import ChatAgent
from agent_framework.openai import OpenAIChatClient


class BaseAgent:
    """Agent Framework 기반 Agent 래퍼"""
    
    def __init__(
        self, 
        name: str, 
        instructions: str,
        tools: Optional[List[Callable]] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Args:
            name: Agent 이름
            instructions: Agent 동작 지침
            tools: Agent가 사용할 도구 함수 리스트
            config: Agent 설정
        """
        self.name = name
        self.config = config or {}
        self.logger = logging.getLogger(f"agent.{name}")
        
        # OpenAI 클라이언트 설정
        api_key = self.config.get("openai_api_key", "your-api-key")
        model = self.config.get("model", "gpt-4")
        
        # ChatAgent 초기화
        self.agent = ChatAgent(
            chat_client=OpenAIChatClient(
                model_id=model,
                api_key=api_key,
            ),
            instructions=instructions,
            tools=tools or [],
            name=name
        )
    
    async def run(self, task: str, **kwargs) -> Any:
        """
        Agent 실행
        
        Args:
            task: 실행할 작업 설명
            **kwargs: 추가 파라미터
            
        Returns:
            실행 결과
        """
        try:
            self.log_info(f"작업 시작: {task}")
            result = await self.agent.run(task)
            self.log_info(f"작업 완료")
            return result
        except Exception as e:
            self.log_error(f"작업 실패: {task}", exc_info=e)
            raise
    
    def log_info(self, message: str):
        """정보 로그"""
        self.logger.info(f"[{self.name}] {message}")
    
    def log_error(self, message: str, exc_info=None):
        """에러 로그"""
        self.logger.error(f"[{self.name}] {message}", exc_info=exc_info)
    
    def log_warning(self, message: str):
        """경고 로그"""
        self.logger.warning(f"[{self.name}] {message}")
