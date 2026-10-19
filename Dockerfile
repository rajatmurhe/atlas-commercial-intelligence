FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app/services/api PORT=8080
WORKDIR /app
COPY services/api/requirements.txt /app/services/api/requirements.txt
RUN pip install --no-cache-dir -r services/api/requirements.txt && useradd --create-home atlas
COPY services/api /app/services/api
COPY database /app/database
COPY scripts /app/scripts
USER atlas
EXPOSE 8080
CMD ["sh", "-c", "exec uvicorn ciq.main:app --host 0.0.0.0 --port ${PORT}"]
