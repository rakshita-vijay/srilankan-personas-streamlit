# Dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY . /app

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

EXPOSE 8080
CMD ["streamlit", "run", "r_optimized.py", "--server.port=8080", "--server.headless=true"]
