FROM python:3.13-slim

WORKDIR /app

COPY pyproject.toml ./
COPY uv.lock ./
COPY README.md ./
RUN pip install uv && uv pip install --system --break-system-packages .

COPY backend/app ./app

EXPOSE 8000

ENV HOST=0.0.0.0 PORT=8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
