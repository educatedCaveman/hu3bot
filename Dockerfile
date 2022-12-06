#Hu3bot
# FROM python:3.10-slim-bullseye
FROM python:latest
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
COPY . .
CMD [ "python", "hu3bot.py"]