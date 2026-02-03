"""
Agent 관리 API 엔드포인트
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Agent 인스턴스들을 관리하기 위한 레지스트리
agent_registry: Dict[str, Any] = {}

router = APIRouter(prefix="/agents", tags=["agents"])


class AgentRequest(BaseModel):
    """Agent 실행 요청"""
    agent_type: str
    action: str
    params: Optional[Dict[str, Any]] = None


class AgentResponse(BaseModel):
    """Agent 응답"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None
    agent_info: Optional[Dict[str, Any]] = None


@router.post("/execute", response_model=AgentResponse)
async def execute_agent(request: AgentRequest) -> AgentResponse:
    """
    Agent 실행
    
    Args:
        request: Agent 실행 요청
        
    Returns:
        Agent 실행 결과
    """
    try:
        # Agent 레지스트리에서 Agent 가져오기
        agent = agent_registry.get(request.agent_type)
        
        if not agent:
            raise HTTPException(
                status_code=404,
                detail=f"Agent not found: {request.agent_type}"
            )
        
        # Agent 실행
        task = f"{request.action}"
        if request.params:
            task += f" with params: {request.params}"
        
        result = await agent.run(task, **(request.params or {}))
        
        return AgentResponse(
            success=True,
            data=result,
            execution_time=agent.last_execution_time,
            agent_info=agent.get_status()
        )
        
    except Exception as e:
        return AgentResponse(
            success=False,
            error=str(e)
        )


@router.get("/status/{agent_type}")
async def get_agent_status(agent_type: str) -> Dict[str, Any]:
    """
    특정 Agent 상태 조회
    
    Args:
        agent_type: Agent 타입
        
    Returns:
        Agent 상태 정보
    """
    agent = agent_registry.get(agent_type)
    
    if not agent:
        raise HTTPException(
            status_code=404,
            detail=f"Agent not found: {agent_type}"
        )
    
    return agent.get_status()


@router.get("/status")
async def get_all_agents_status() -> Dict[str, Any]:
    """
    모든 Agent 상태 조회
    
    Returns:
        모든 Agent 상태 정보
    """
    return {
        agent_type: agent.get_status()
        for agent_type, agent in agent_registry.items()
    }


@router.get("/health")
async def health_check() -> Dict[str, bool]:
    """
    Agent 헬스체크
    
    Returns:
        각 Agent의 건강 상태
    """
    return {
        agent_type: agent.health_check()
        for agent_type, agent in agent_registry.items()
    }


def register_agent(agent_type: str, agent: Any):
    """
    Agent 레지스트리에 Agent 등록
    
    Args:
        agent_type: Agent 타입
        agent: Agent 인스턴스
    """
    agent_registry[agent_type] = agent


def get_agent(agent_type: str) -> Optional[Any]:
    """
    Agent 레지스트리에서 Agent 가져오기
    
    Args:
        agent_type: Agent 타입
        
    Returns:
        Agent 인스턴스 또는 None
    """
    return agent_registry.get(agent_type)
