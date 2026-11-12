FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml requirements.lock ./
COPY src ./src
RUN pip install --no-cache-dir -r requirements.lock && pip install --no-deps . && useradd -m appuser
USER appuser
ENV COPILOT_DB=/data/energy.db
ENV FASTEMBED_CACHE_PATH=/home/appuser/.cache/fastembed
EXPOSE 8000
CMD ["uvicorn", "energy_copilot.api:app", "--host", "0.0.0.0", "--port", "8000"]
