FROM python:3.14-slim

WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY api/ api/

ENV PYTHONUNBUFFERED=1
CMD ["python", "-m", "api.server"]
