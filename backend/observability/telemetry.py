"""
Application Insights 및 OpenTelemetry 텔레메트리 설정

Application Insights 테이블 매핑:
- requests: HTTP 요청 (FastAPI 자동 계측) → requests 테이블
- dependencies: 외부 API 호출 (HTTPX, Cosmos DB 등) → dependencies 테이블
- traces: 로그 메시지 (logger.info/warning/error) → traces 테이블
- pageViews: 페이지 뷰 (TelemetryClient.track_pageview) → pageViews 테이블
- customEvents: 사용자 이벤트 (TelemetryClient.track_event) → customEvents 테이블
- customMetrics: 커스텀 메트릭 (OpenTelemetry Metrics) → customMetrics 테이블
- exceptions: 예외 (span.record_exception) → exceptions 테이블
"""
import logging
import os
from datetime import datetime, timedelta

from applicationinsights import TelemetryClient
from applicationinsights.channel import TelemetryChannel
from azure.monitor.opentelemetry import configure_azure_monitor
from dotenv import load_dotenv
from opentelemetry import metrics, trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.resources import Resource

load_dotenv()
logger = logging.getLogger(__name__)

# Application Insights TelemetryClient (pageViews 및 customEvents 전송용)
_telemetry_client: TelemetryClient | None = None

# Azure SDK tracing을 위한 import
try:
    from azure.core.settings import settings as azure_settings
    from azure.core.tracing.ext.opentelemetry_span import OpenTelemetrySpan
    AZURE_TRACING_AVAILABLE = True
except ImportError:
    AZURE_TRACING_AVAILABLE = False
    logger.warning("Azure Core tracing not available")

# Azure SDK HTTP 로깅 비활성화
logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.WARNING)
logging.getLogger("azure.monitor.opentelemetry").setLevel(logging.WARNING)
logging.getLogger("azure.monitor.opentelemetry.exporter._configuration").setLevel(logging.ERROR)
logging.getLogger("opentelemetry").setLevel(logging.WARNING)


def setup_telemetry(app=None):
    """
    Application Insights 텔레메트리 설정
    환경변수 APPLICATIONINSIGHTS_CONNECTION_STRING 필요
    
    테이블별 데이터 수집:
    - requests: FastAPI 요청 (자동)
    - dependencies: 외부 API 호출 (HTTPX, Cosmos DB - 자동)
    - traces: Python 로거 출력 (자동)
    - pageViews: track_page_view() 호출
    - customEvents: track_user_event() 호출
    - customMetrics: OpenTelemetry Metrics (자동)
    - exceptions: 예외 발생 시 (자동)
    
    Args:
        app: FastAPI 앱 인스턴스 (선택적)
    """
    global _telemetry_client
    
    connection_string = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
    
    if not connection_string:
        logger.warning("APPLICATIONINSIGHTS_CONNECTION_STRING not set. Telemetry disabled.")
        return
    
    try:
        # Application Insights TelemetryClient 초기화
        # pageViews 테이블과 customEvents 테이블에 데이터 전송
        instrumentation_key = None
        for part in connection_string.split(';'):
            if part.startswith('InstrumentationKey='):
                instrumentation_key = part.split('=')[1]
                break
        
        if instrumentation_key:
            _telemetry_client = TelemetryClient(instrumentation_key)
            # 즉시 전송 설정 (개발 환경용)
            _telemetry_client.channel.flush()
            logger.info("✅ TelemetryClient initialized → pageViews, customEvents 테이블")
        
        # 서비스 이름 결정: FastAPI 앱이 제공되면 앱 제목 사용, 아니면 기본값
        service_name = app.title if app and hasattr(app, 'title') else "etf-agent"
        service_version = app.version if app and hasattr(app, 'version') else "0.1.0"
        
        # 환경변수에서 deployment.environment 가져오기
        deployment_environment = os.getenv("DEPLOYMENT_ENVIRONMENT", "development")
        
        # 리소스 속성 정의
        resource = Resource.create({
            "service.name": service_name,
            "service.version": service_version,
            "deployment.environment": deployment_environment,
        })
        
        # Azure Monitor OpenTelemetry 설정
        # requests, dependencies, traces, customMetrics, exceptions 테이블에 데이터 전송
        configure_azure_monitor(
            connection_string=connection_string,
            enable_live_metrics=True,
            resource=resource,
        )
        
        # Python 로깅을 traces 테이블로 전송하기 위한 설정
        # configure_azure_monitor가 자동으로 LoggingHandler를 설정하므로
        # 루트 로거의 레벨을 INFO로 설정하여 로그가 수집되도록 함
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        
        # 애플리케이션 로거들도 INFO 레벨로 설정
        app_loggers = ["show-me-the-money", "etf-agent", "app", "uvicorn.error"]
        for logger_name in app_loggers:
            app_logger = logging.getLogger(logger_name)
            app_logger.setLevel(logging.INFO)
        
        # uvicorn.access 로그는 WARNING 레벨로 설정 (너무 많은 로그 방지)
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
        
        logger.info("✅ Logging handler configured → traces 테이블")
        
        # FastAPI 자동 계측 → requests 테이블
        if app:
            FastAPIInstrumentor.instrument_app(app)
            logger.info("✅ FastAPI instrumented → requests 테이블")
        
        # HTTPX 클라이언트 자동 계측 → dependencies 테이블
        HTTPXClientInstrumentor().instrument()
        logger.info("✅ HTTPX instrumented → dependencies 테이블")
        
        # Azure SDK tracing 활성화 → dependencies 테이블 (Cosmos DB 등)
        try:
            from azure.core.settings import settings as azure_settings
            from azure.core.tracing.ext.opentelemetry_span import \
                OpenTelemetrySpan

            # Azure SDK에서 OpenTelemetry span을 사용하도록 설정
            azure_settings.tracing_implementation = OpenTelemetrySpan
            
            # Cosmos DB dependency를 Application Map에 표시하기 위한 설정
            # peer.service 속성이 자동으로 dependency target name이 됨
            logger.info("✅ Azure SDK tracing enabled → dependencies 테이블 (Cosmos DB → COSMOS)")
        except ImportError:
            logger.warning("Azure Core tracing not available")
        
        logger.info("=" * 80)
        logger.info("📊 Application Insights 텔레메트리 테이블 매핑:")
        logger.info("  - requests: FastAPI HTTP 요청")
        logger.info("  - dependencies: HTTPX API 호출, Cosmos DB 쿼리 (COSMOS)")
        logger.info("  - traces: Python logger 로그 (info/warning/error)")
        logger.info("  - pageViews: track_page_view() 호출")
        logger.info("  - customEvents: track_user_event() 호출")
        logger.info("  - customMetrics: OpenTelemetry Metrics")
        logger.info("  - exceptions: 예외 발생 시 자동 기록")
        logger.info("")
        logger.info("🗺️  Application Map:")
        logger.info(f"  - {service_name} → COSMOS (Cosmos DB)")
        logger.info(f"  - {service_name} → External APIs (yfinance, etc.)")
        logger.info("=" * 80)
    except Exception as e:
        logger.error(f"❌ Error configuring telemetry: {e}")


def get_tracer(name: str):
    """트레이서 가져오기"""
    return trace.get_tracer(name)


def get_meter(name: str):
    """미터 가져오기"""
    return metrics.get_meter(name)


# 애플리케이션 전역 메트릭
_meter = None
_request_counter = None
_request_duration = None
_error_counter = None
_page_view_counter = None
_page_duration_histogram = None
_user_event_counter = None


def initialize_metrics(service_name: str = "etf-agent"):
    """
    커스텀 메트릭 초기화 → customMetrics 테이블
    
    OpenTelemetry Metrics는 customMetrics 테이블에 저장됨
    Live Metrics에도 실시간으로 표시됨
    
    Args:
        service_name: 서비스 이름 (기본값: "etf-agent")
    """
    global _meter, _request_counter, _request_duration, _error_counter
    global _page_view_counter, _page_duration_histogram, _user_event_counter
    
    _meter = metrics.get_meter(f"{service_name}.metrics")
    
    # 요청 카운터 → customMetrics
    _request_counter = _meter.create_counter(
        name="app.requests.total",
        description="Total number of requests",
        unit="1",
    )
    
    # 요청 처리 시간 → customMetrics
    _request_duration = _meter.create_histogram(
        name="app.requests.duration",
        description="Request duration in milliseconds",
        unit="ms",
    )
    
    # 에러 카운터 → customMetrics
    _error_counter = _meter.create_counter(
        name="app.errors.total",
        description="Total number of errors",
        unit="1",
    )
    
    # 페이지 뷰 카운터 → customMetrics
    _page_view_counter = _meter.create_counter(
        name="app.page_views.total",
        description="Total number of page views",
        unit="1",
    )
    
    # 페이지 체류 시간 히스토그램 → customMetrics
    _page_duration_histogram = _meter.create_histogram(
        name="app.page_views.duration",
        description="Page view duration in seconds",
        unit="s",
    )
    
    # 사용자 이벤트 카운터 → customMetrics
    _user_event_counter = _meter.create_counter(
        name="app.user_events.total",
        description="Total number of user events",
        unit="1",
    )
    
    logger.info("📈 Custom metrics initialized → customMetrics 테이블")


def record_request(endpoint: str, method: str, status_code: int, duration_ms: float):
    """
    요청 메트릭 기록 → customMetrics 테이블
    Live Metrics에도 실시간 표시
    """
    if _request_counter and _request_duration:
        attributes = {
            "endpoint": endpoint,
            "method": method,
            "status_code": str(status_code),
        }
        _request_counter.add(1, attributes)
        _request_duration.record(duration_ms, attributes)


def record_error(error_type: str, endpoint: str | None = None):
    """
    에러 메트릭 기록 → customMetrics 테이블
    Live Metrics에도 실시간 표시
    """
    if _error_counter:
        attributes = {"error_type": error_type}
        if endpoint:
            attributes["endpoint"] = endpoint
        _error_counter.add(1, attributes)


def track_page_view(name: str, url: str = "", properties: dict | None = None, duration_ms: int | None = None):
    """
    페이지 뷰 추적 → pageViews 테이블
    
    Application Insights의 표준 pageViews 테이블에 저장됩니다.
    KQL 쿼리: pageViews | where name == "Dashboard"
    
    Args:
        name: 페이지 이름 (예: "Dashboard", "ETF List")
        url: 페이지 URL (선택적)
        properties: 커스텀 속성 (user_id, session_id 등)
        duration_ms: 페이지 체류 시간 (밀리초)
    """
    if not _telemetry_client:
        logger.warning("TelemetryClient not initialized. Cannot track page view.")
        return
    
    try:
        # properties에 duration 정보 추가 (duration 필드 대신)
        props = properties.copy() if properties else {}
        if duration_ms is not None and duration_ms > 0:
            props["duration_ms"] = str(duration_ms)
            props["duration_seconds"] = str(duration_ms / 1000)
        
        # pageViews 테이블에 표준 형식으로 저장
        # duration=0: Application Insights SDK의 duration 형식 오류 방지
        _telemetry_client.track_pageview(
            name=name,
            url=url or f"/{name.lower().replace(' ', '-')}",
            duration=0,  # customDimensions에 저장
            properties=props,
        )
        
        # 즉시 전송 (개발 환경용)
        _telemetry_client.flush()
        
        # customMetrics 테이블에도 카운터 기록
        if _page_view_counter:
            metric_attributes = {"page_name": name}
            if properties:
                for key in ["user_id", "session_id"]:
                    if key in properties:
                        metric_attributes[key] = str(properties[key])
            _page_view_counter.add(1, metric_attributes)
        
        # 페이지 체류 시간을 customMetrics에 기록
        if duration_ms and _page_duration_histogram:
            _page_duration_histogram.record(
                duration_ms / 1000,
                {"page_name": name}
            )
        
        # traces 테이블에 로그 기록
        log_msg = f"📄 Page view: {name}"
        if duration_ms:
            log_msg += f" ({duration_ms}ms)"
        if properties:
            log_msg += f" | user: {properties.get('user_id', 'N/A')[:8]}..."
        logger.info(log_msg)
        
    except Exception as e:
        logger.error(f"Failed to track page view: {e}")


def track_user_event(name: str, properties: dict | None = None, measurements: dict | None = None):
    """
    사용자 이벤트 추적 → customEvents 테이블
    
    Application Insights의 표준 customEvents 테이블에 저장됩니다.
    KQL 쿼리: customEvents | where name == "button_click"
    
    Args:
        name: 이벤트 이름 (예: "button_click", "search", "filter_applied")
        properties: 문자열 속성 (event_category, user_id 등)
        measurements: 숫자 측정값 (search_results_count 등)
    """
    if not _telemetry_client:
        logger.warning("TelemetryClient not initialized. Cannot track event.")
        return
    
    try:
        # customEvents 테이블에 표준 형식으로 저장
        _telemetry_client.track_event(
            name=name,
            properties=properties or {},
            measurements=measurements or {},
        )
        
        # 즉시 전송 (개발 환경용)
        _telemetry_client.flush()
        
        # customMetrics 테이블에도 카운터 기록
        if _user_event_counter:
            metric_attributes = {"event_name": name}
            if properties:
                for key in ["event_category", "user_id", "session_id"]:
                    if key in properties:
                        metric_attributes[key] = str(properties[key])
            _user_event_counter.add(1, metric_attributes)
        
        # traces 테이블에 로그 기록
        log_msg = f"🎯 User event: {name}"
        if properties:
            category = properties.get("event_category", "N/A")
            log_msg += f" | category: {category}"
            if "user_id" in properties:
                log_msg += f" | user: {properties['user_id'][:8]}..."
        logger.info(log_msg)
        
    except Exception as e:
        logger.error(f"Failed to track event: {e}")


def track_exception(exception: Exception, properties: dict | None = None):
    """
    예외 추적 → exceptions 테이블
    
    Args:
        exception: 예외 객체
        properties: 추가 속성
    """
    if not _telemetry_client:
        logger.warning("TelemetryClient not initialized. Cannot track exception.")
        return
    
    try:
        _telemetry_client.track_exception(
            type(exception),
            exception,
            exception.__traceback__,
            properties=properties or {},
        )
        _telemetry_client.flush()
        logger.error(f"Exception tracked: {exception}", exc_info=True)
    except Exception as e:
        logger.error(f"Failed to track exception: {e}")
