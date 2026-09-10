FROM python:3.12-slim

WORKDIR /app
COPY olivia_bridge.py /app/olivia_bridge.py

ENV OLIVIA_HOST=0.0.0.0
ENV OLIVIA_PORT=10000

EXPOSE 10000
CMD ["python", "olivia_bridge.py"]
