FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir awslambdaric

COPY . .

RUN python3 database.py

ENTRYPOINT ["python3", "-m", "awslambdaric"]
CMD ["lambda_handler.handler"]