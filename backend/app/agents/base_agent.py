"""
Base Agent 클래스
Microsoft Agent Framework 기반의 Agent 구조
"""

import logging
import time
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from agent_framework import ChatAgent
from agent_framework.openai import OpenAIChatClient


class AgentStatus(str, Enum):
    """Agent 상태"""
    IDLE = "idle"
    RUNNING = "running"
    ERROR = "error"
    STOPPED = "stopped"


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
        self.status = AgentStatus.IDLE
        self.version = self.config.get("version", "1.0.0")
        self.last_execution_time: Optional[float] = None
        self.execution_count = 0
        self.error_count = 0
        
        # OpenAI 클라이언트 설정
        api_key = self.config.get("openai_api_key", "your-api-key")
        model = self.config.get("model", "gpt-4")
        
        # ChatAgent 초기화 (Agent Framework가 설치되어 있을 때만)
        try:
            self.agent = ChatAgent(
                chat_client=OpenAIChatClient(
                    model_id=model,
                    api_key=api_key,
                ),
                instructions=instructions,
                tools=tools or [],
                name=name
            )
        except Exception as e:
            self.log_warning(f"ChatAgent 초기화 실패 (Agent Framework 미설치 가능): {e}")
            self.agent = None
    
    async def run(self, task: str, **kwargs) -> Any:
        """
        Agent 실행
        
        Args:
            task: 실행할 작업 설명
            **kwargs: 추가 파라미터
            
        Returns:
            실행 결과
        """
        start_time = time.time()
        self.status = AgentStatus.RUNNING
        
        try:
            self.log_info(f"작업 시작: {task}")
            
            if self.agent:
                result = await self.agent.run(task)
            else:
                # Agent Framework가 없을 때는 기본 동작 수행
                result = await self._execute_fallback(task, **kwargs)
            
            execution_time = time.time() - start_time
            self.last_execution_time = execution_time
            self.execution_count += 1
            self.status = AgentStatus.IDLE
            
            self.log_info(f"작업 완료 (실행 시간: {execution_time:.2f}초)")
            return result
            
        except Exception as e:
            self.error_count += 1
            self.status = AgentStatus.ERROR
            self.log_error(f"작업 실패: {task}", exc_info=e)
            raise
    
    async def _execute_fallback(self, task: str, **kwargs) -> Any:
        """
        Agent Framework가 없을 때 대체 실행
        하위 클래스에서 구현
        """
        raise NotImplementedError("_execute_fallback must be implemented by subclass")
    
    def get_status(self) -> Dict[str, Any]:
        """Agent 상태 정보 반환"""
        return {
            "name": self.name,
            "version": self.version,
            "status": self.status.value,
            "execution_count": self.execution_count,
            "error_count": self.error_count,
            "last_execution_time": self.last_execution_time,
            "uptime": datetime.now().isoformat(),
        }
    
    def health_check(self) -> bool:
        """Agent 건강 상태 체크"""
        return self.status != AgentStatus.ERROR
    
    def reset_metrics(self):
        """메트릭 초기화"""
        self.execution_count = 0
        self.error_count = 0
        self.last_execution_time = None
    
    def log_info(self, message: str):
        """정보 로그"""
        self.logger.info(f"[{self.name}] {message}")
    
    def log_error(self, message: str, exc_info=None):
        """에러 로그"""
        self.logger.error(f"[{self.name}] {message}", exc_info=exc_info)
    
    def log_warning(self, message: str):
        """경고 로그"""
        self.logger.warning(f"[{self.name}] {message}")
    
    def log_debug(self, message: str):
        """디버그 로그"""
        self.logger.debug(f"[{self.name}] {message}")
