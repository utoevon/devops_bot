FROM python:3.9-slim

WORKDIR /code

COPY requirements.txt requirements.txt
COPY bot.py bot.py
RUN mkdir /var/log/postgresql
RUN chmod -R 777 /var/log/postgresql
RUN pip install -r requirements.txt

CMD ["python", "bot.py"]