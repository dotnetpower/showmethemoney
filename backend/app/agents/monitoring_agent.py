"""
Monitoring Agent
Application Insights를 통해 애플리케이션 상태를 모니터링하는 Agent
Microsoft Agent Framework 기반
"""

import logging
from datetime import datetime, timedelta
from typing import Annotated, Any, Dict, List, Optional

from pydantic import Field

from .base_agent import BaseAgent

try:
    from azure.monitor.opentelemetry import configure_azure_monitor
    from opentelemetry import metrics, trace
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.trace import TracerProvider
    AZURE_MONITOR_AVAILABLE = True
except ImportError:
    AZURE_MONITOR_AVAILABLE = False


def track_metric_data(
    metric_name: Annotated[str, Field(description="메트릭 이름")],
    value: Annotated[float, Field(description="메트릭 값")]
) -> str:
    """메트릭 데이터 추적"""
    return f"Tracked metric: {metric_name} = {value}"


class MonitoringAgent(BaseAgent):
    """모니터링 Agent"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        config = config or {}
        
        instructions = """
        당신은 Application Insights를 활용한 모니터링 전문 Agent입니다.
        
        주요 역할:
        1. API 요청 및 성능 메트릭 추적
        2. 에러 및 예외 상황 모니터링
        3. 애플리케이션 상태 확인
        4. 성능 지표 수집 및 분석
        
        모니터링 항목:
        - API 요청 수 및 응답 시간
        - 에러 발생 빈도
        - 리소스 사용량
        - 애플리케이션 상태
        """
        
        tools = [track_metric_data]
        
        super().__init__(
            name="Monitoring",
            instructions=instructions,
            tools=tools,
            config=config
        )
        
        self.connection_string = config.get("connection_string")
        self.metrics_data = []
        self.traces_data = []
        
        # Azure Monitor 초기화
        if AZURE_MONITOR_AVAILABLE and self.connection_string:
            self._initialize_azure_monitor()
        
        # Tracer 및 Meter 설정
        self.tracer = trace.get_tracer(__name__)
        self.meter = metrics.get_meter(__name__)
        
        # 메트릭 정의
        self.request_counter = self.meter.create_counter(
            "api_requests",
            description="API 요청 수"
        )
        self.error_counter = self.meter.create_counter(
            "errors",
            description="에러 발생 수"
        )
        self.latency_histogram = self.meter.create_histogram(
            "request_latency",
            description="요청 처리 시간 (ms)"
        )
        
    def _initialize_azure_monitor(self):
        """Azure Monitor 초기화"""
        try:
            configure_azure_monitor(
                connection_string=self.connection_string
            )
            self.log_info("Azure Monitor 초기화 완료")
        except Exception as e:
            self.log_error("Azure Monitor 초기화 실패", exc_info=e)
    
    async def execute(self, operation: str, **kwargs) -> Dict[str, Any]:
        """
        모니터링 작업 실행
        
        Args:
            operation: 작업 타입
            **kwargs: 작업 파라미터
            
        Returns:
            작업 결과
        """
        try:
            self.log_info(f"모니터링 작업 시작: {operation}")
            
            if not await self.validate(operation=operation, **kwargs):
                raise ValueError("유효하지 않은 작업")
            
            if operation == "track_request":
                result = await self._track_request(**kwargs)
            elif operation == "track_error":
                result = await self._track_error(**kwargs)
            elif operation == "track_metric":
                result = await self._track_metric(**kwargs)
            elif operation == "get_metrics":
                result = await self._get_metrics(**kwargs)
            elif operation == "get_health":
                result = await self._get_health(**kwargs)
            else:
                raise ValueError(f"지원하지 않는 작업: {operation}")
            
            self.log_info(f"모니터링 작업 완료: {operation}")
            return result
            
        except Exception as e:
            self.log_error(f"모니터링 작업 실패: {operation}", exc_info=e)
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
        valid_operations = [
            "track_request",
            "track_error",
            "track_metric",
            "get_metrics",
            "get_health"
        ]
        
        if operation not in valid_operations:
            return False
        
        return True
    
    async def _track_request(
        self,
        name: str,
        duration: float,
        success: bool = True,
        **properties
    ) -> Dict[str, Any]:
        """
        API 요청 추적
        
        Args:
            name: 요청 이름
            duration: 처리 시간 (ms)
            success: 성공 여부
            **properties: 추가 속성
            
        Returns:
            추적 결과
        """
        with self.tracer.start_as_current_span(name) as span:
            span.set_attribute("duration_ms", duration)
            span.set_attribute("success", success)
            
            for key, value in properties.items():
                span.set_attribute(key, value)
        
        # 메트릭 기록
        self.request_counter.add(1, {"name": name, "success": str(success)})
        self.latency_histogram.record(duration, {"name": name})
        
        # 로컬 저장
        self.metrics_data.append({
            "type": "request",
            "name": name,
            "duration": duration,
            "success": success,
            "timestamp": datetime.utcnow().isoformat(),
            **properties
        })
        
        return {
            "operation": "track_request",
            "name": name,
            "status": "success"
        }
    
    async def _track_error(
        self,
        error_type: str,
        message: str,
        **properties
    ) -> Dict[str, Any]:
        """
        에러 추적
        
        Args:
            error_type: 에러 타입
            message: 에러 메시지
            **properties: 추가 속성
            
        Returns:
            추적 결과
        """
        with self.tracer.start_as_current_span("error") as span:
            span.set_attribute("error_type", error_type)
            span.set_attribute("message", message)
            span.record_exception(Exception(message))
            
            for key, value in properties.items():
                span.set_attribute(key, value)
        
        # 메트릭 기록
        self.error_counter.add(1, {"error_type": error_type})
        
        # 로컬 저장
        self.metrics_data.append({
            "type": "error",
            "error_type": error_type,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            **properties
        })
        
        # 에러 로그
        self.log_error(f"{error_type}: {message}")
        
        return {
            "operation": "track_error",
            "error_type": error_type,
            "status": "success"
        }
    
    async def _track_metric(
        self,
        name: str,
        value: float,
        **properties
    ) -> Dict[str, Any]:
        """
        커스텀 메트릭 추적
        
        Args:
            name: 메트릭 이름
            value: 메트릭 값
            **properties: 추가 속성
            
        Returns:
            추적 결과
        """
        # 로컬 저장
        self.metrics_data.append({
            "type": "metric",
            "name": name,
            "value": value,
            "timestamp": datetime.utcnow().isoformat(),
            **properties
        })
        
        return {
            "operation": "track_metric",
            "name": name,
            "value": value,
            "status": "success"
        }
    
    async def _get_metrics(
        self,
        metric_type: Optional[str] = None,
        since: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        메트릭 조회
        
        Args:
            metric_type: 메트릭 타입 필터
            since: 시작 시간
            
        Returns:
            메트릭 데이터
        """
        filtered_data = self.metrics_data
        
        if metric_type:
            filtered_data = [m for m in filtered_data if m.get("type") == metric_type]
        
        if since:
            filtered_data = [
                m for m in filtered_data
                if datetime.fromisoformat(m["timestamp"]) >= since
            ]
        
        return {
            "operation": "get_metrics",
            "data": filtered_data,
            "count": len(filtered_data),
            "status": "success"
        }
    
    async def _get_health(self) -> Dict[str, Any]:
        """
        애플리케이션 헬스 체크
        
        Returns:
            헬스 상태
        """
        # 최근 에러 확인 (지난 5분)
        five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)
        recent_errors = [
            m for m in self.metrics_data
            if m.get("type") == "error" and
            datetime.fromisoformat(m["timestamp"]) >= five_minutes_ago
        ]
        
        # 평균 응답 시간 계산
        recent_requests = [
            m for m in self.metrics_data
            if m.get("type") == "request" and
            datetime.fromisoformat(m["timestamp"]) >= five_minutes_ago
        ]
        
        avg_latency = 0
        if recent_requests:
            avg_latency = sum(r.get("duration", 0) for r in recent_requests) / len(recent_requests)
        
        # 헬스 상태 결정
        health_status = "healthy"
        if len(recent_errors) > 10:
            health_status = "unhealthy"
        elif len(recent_errors) > 5 or avg_latency > 1000:
            health_status = "degraded"
        
        return {
            "operation": "get_health",
            "status": health_status,
            "details": {
                "recent_errors": len(recent_errors),
                "avg_latency_ms": avg_latency,
                "total_requests": len(recent_requests)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def start_trace(self, name: str):
        """
        트레이스 시작
        
        Args:
            name: 트레이스 이름
            
        Returns:
            Span 컨텍스트
        """
        return self.tracer.start_as_current_span(name)
