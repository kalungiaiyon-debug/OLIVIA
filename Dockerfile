FROM python:3.12-slim

WORKDIR /app
COPY olivia_bridge.py /app/olivia_bridge.py
COPY web_ui.html /app/web_ui.html
COPY assets /app/assets

ENV OLIVIA_HOST=0.0.0.0
ENV OLIVIA_PORT=10000

EXPOSE 10000
CMD ["python", "olivia_bridge.py"]
