FROM python:3.9-slim

WORKDIR /app
COPY . .
RUN pip install -r /app/requirements.txt

CMD ["python", "connector.py"]