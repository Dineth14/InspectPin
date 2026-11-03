FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY inspectpin inspectpin
COPY receiver.py .
ENV HOST=0.0.0.0 PORT=5000 DATA_DIR=/data STT_PROVIDER=mock LLM_PROVIDER=mock TTS_PROVIDER=mock VISION_PROVIDER=mock
VOLUME ["/data"]
EXPOSE 5000
CMD ["python", "receiver.py"]
