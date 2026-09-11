FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    KILL_SCAM_HOSTED=1

COPY pyproject.toml README.md ./
COPY src ./src
COPY .streamlit ./.streamlit

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

EXPOSE 8080

CMD ["sh", "-c", "streamlit run src/kill_scam/app.py --server.port=${PORT:-8080} --server.address=0.0.0.0 --server.headless=true"]
