FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app
WORKDIR /app
COPY services/multi_ai_router/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
COPY services/multi_ai_router /app/multi_ai_router
RUN useradd --create-home --uid 10001 helpus && chown -R helpus:helpus /app
USER helpus
EXPOSE 8080
CMD ["uvicorn","multi_ai_router.app:app","--host","0.0.0.0","--port","8080","--proxy-headers"]
