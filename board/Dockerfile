FROM python:3.11-slim

WORKDIR /board/

COPY . .

RUN pip install -r requirements.txt

CMD uvicorn main:app --reload --host 0.0.0.0