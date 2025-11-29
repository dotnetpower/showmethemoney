"""
Observability 유틸리티 함수
"""
import functools
import inspect
from typing import Any, Callable, Optional

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

tracer = trace.get_tracer(__name__)


def trace_span(
    name: Optional[str] = None,
    attributes: Optional[dict] = None,
    kind: trace.SpanKind = trace.SpanKind.INTERNAL
):
    """
    함수 실행을 추적하는 데코레이터 - End-to-end transaction details에 함수 레벨 추적
    
    Application Insights의 End-to-end transaction에 함수 호출이 개별 span으로 표시됩니다.
    각 함수의 실행 시간, 매개변수, 결과, 예외가 자동으로 기록됩니다.
    
    Args:
        name: 스팬 이름 (기본값: 클래스명.함수명)
        attributes: 추가할 속성들
        kind: 스팬 종류 (INTERNAL=내부 함수, CLIENT=외부 호출)
    
    Example:
        @trace_span(name="get_stock_data", attributes={"source": "yfinance"})
        async def get_stock(symbol: str):
            ...
    """
    def decorator(func: Callable) -> Callable:
        # 클래스 메서드인 경우 클래스명 포함
        func_name = func.__name__
        module_name = func.__module__.replace('src.', '')  # src. 접두사 제거
        span_name = name or f"{module_name}.{func_name}"
        
        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs) -> Any:
                with tracer.start_as_current_span(
                    span_name,
                    kind=kind
                ) as span:
                    # 기본 속성 추가 (End-to-end transaction에 표시)
                    span.set_attribute("code.function", func.__name__)
                    span.set_attribute("code.namespace", func.__module__)
                    try:
                        span.set_attribute("code.filepath", inspect.getfile(func))
                    except:
                        pass
                    
                    # 클래스 메서드인 경우 클래스명 추가
                    if args and hasattr(args[0], '__class__'):
                        class_name = args[0].__class__.__name__
                        if class_name not in ['str', 'int', 'float', 'bool', 'list', 'dict']:
                            span.set_attribute("code.class", class_name)
                    
                    # 사용자 정의 속성 추가
                    if attributes:
                        for key, value in attributes.items():
                            span.set_attribute(key, value)
                    
                    # 함수 인자를 속성으로 추가 (문자열이나 숫자만, self/cls 제외)
                    # End-to-end transaction에서 각 함수 호출의 매개변수 확인 가능
                    arg_start = 1 if args and hasattr(args[0], '__class__') else 0
                    for i, arg in enumerate(args[arg_start:], start=arg_start):
                        if isinstance(arg, (str, int, float, bool)):
                            arg_str = str(arg)[:200]  # 최대 200자
                            span.set_attribute(f"function.arg{i}", arg_str)
                    
                    for key, value in kwargs.items():
                        if isinstance(value, (str, int, float, bool)):
                            value_str = str(value)[:200]  # 최대 200자
                            span.set_attribute(f"function.param.{key}", value_str)
                        elif isinstance(value, (list, dict)):
                            span.set_attribute(f"function.param.{key}.type", type(value).__name__)
                            span.set_attribute(f"function.param.{key}.length", len(value))
                    
                    try:
                        import time
                        start_time = time.time()
                        
                        result = await func(*args, **kwargs)
                        
                        # 실행 시간 기록
                        duration_ms = (time.time() - start_time) * 1000
                        span.set_attribute("function.duration_ms", round(duration_ms, 2))
                        
                        # 결과 타입 기록
                        if result is not None:
                            span.set_attribute("function.result.type", type(result).__name__)
                            if isinstance(result, (list, dict)):
                                span.set_attribute("function.result.length", len(result))
                            elif isinstance(result, (str, int, float, bool)):
                                result_str = str(result)[:100]
                                span.set_attribute("function.result.value", result_str)
                        
                        span.set_status(Status(StatusCode.OK))
                        return result
                    except Exception as e:
                        # 예외 정보 상세 기록 (End-to-end transaction에서 오류 추적)
                        span.set_status(Status(StatusCode.ERROR, str(e)))
                        span.set_attribute("error.type", type(e).__name__)
                        span.set_attribute("error.message", str(e)[:500])
                        span.record_exception(e)
                        raise
            
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs) -> Any:
                with tracer.start_as_current_span(
                    span_name,
                    kind=kind
                ) as span:
                    # 기본 속성 추가
                    span.set_attribute("code.function", func.__name__)
                    span.set_attribute("code.namespace", func.__module__)
                    try:
                        span.set_attribute("code.filepath", inspect.getfile(func))
                    except:
                        pass
                    
                    # 클래스 메서드인 경우 클래스명 추가
                    if args and hasattr(args[0], '__class__'):
                        class_name = args[0].__class__.__name__
                        if class_name not in ['str', 'int', 'float', 'bool', 'list', 'dict']:
                            span.set_attribute("code.class", class_name)
                    
                    # 사용자 정의 속성 추가
                    if attributes:
                        for key, value in attributes.items():
                            span.set_attribute(key, value)
                    
                    # 함수 인자를 속성으로 추가 (self/cls 제외)
                    arg_start = 1 if args and hasattr(args[0], '__class__') else 0
                    for i, arg in enumerate(args[arg_start:], start=arg_start):
                        if isinstance(arg, (str, int, float, bool)):
                            arg_str = str(arg)[:200]
                            span.set_attribute(f"function.arg{i}", arg_str)
                    
                    for key, value in kwargs.items():
                        if isinstance(value, (str, int, float, bool)):
                            value_str = str(value)[:200]
                            span.set_attribute(f"function.param.{key}", value_str)
                        elif isinstance(value, (list, dict)):
                            span.set_attribute(f"function.param.{key}.type", type(value).__name__)
                            span.set_attribute(f"function.param.{key}.length", len(value))
                    
                    try:
                        import time
                        start_time = time.time()
                        
                        result = func(*args, **kwargs)
                        
                        # 실행 시간 기록
                        duration_ms = (time.time() - start_time) * 1000
                        span.set_attribute("function.duration_ms", round(duration_ms, 2))
                        
                        # 결과 타입 기록
                        if result is not None:
                            span.set_attribute("function.result.type", type(result).__name__)
                            if isinstance(result, (list, dict)):
                                span.set_attribute("function.result.length", len(result))
                            elif isinstance(result, (str, int, float, bool)):
                                result_str = str(result)[:100]
                                span.set_attribute("function.result.value", result_str)
                        
                        span.set_status(Status(StatusCode.OK))
                        return result
                    except Exception as e:
                        span.set_status(Status(StatusCode.ERROR, str(e)))
                        span.set_attribute("error.type", type(e).__name__)
                        span.set_attribute("error.message", str(e)[:500])
                        span.record_exception(e)
                        raise
            
            return sync_wrapper
    
    return decorator
