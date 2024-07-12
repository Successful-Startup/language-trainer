FROM python:3.12-slim

ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

# Устанавливаем права доступа к файлу django.sh
RUN chmod +x /app/django.sh

EXPOSE 8000

ENTRYPOINT [ "/app/django.sh" ]