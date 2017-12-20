FROM python:2.7
LABEL maintainer="Paul Schifferer <paul@schifferers.net>"

RUN apt-get update -y
RUN wget -O /usr/local/bin/dumb-init https://github.com/Yelp/dumb-init/releases/download/v1.2.0/dumb-init_1.2.0_amd64 && chmod +x /usr/local/bin/dumb-init

ADD requirements.txt .
RUN pip install -r ./requirements.txt

COPY app /app

EXPOSE 5000

WORKDIR /app
ENTRYPOINT ["dumb-init"]
CMD ["python", "-u", "app.py"]
