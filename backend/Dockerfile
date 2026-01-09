FROM python:3.13-slim

# 보안: 비특권 사용자 생성
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

COPY pyproject.toml ./
COPY uv.lock ./
COPY README.md ./
RUN pip install uv && uv pip install --system --break-system-packages .

COPY backend/app ./app
# Copy observability module for Application Insights
COPY backend/observability ./observability
# Copy data directory to the image
COPY data ./data

# 보안: 애플리케이션 디렉토리 소유권 변경
RUN chown -R appuser:appuser /app

# 보안: 비특권 사용자로 전환
USER appuser

EXPOSE 8000

ENV HOST=0.0.0.0 PORT=8000
# Set data directory path
ENV DATA_DIR=/app/data

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
