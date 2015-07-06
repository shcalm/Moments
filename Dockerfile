FROM python:2.7.8

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app
COPY . /usr/src/app

RUN pip install -r requirements.txt

EXPOSE 3000
RUN export FLASK_CONFIG=daocloud

CMD [ "gunicorn","-b 0.0.0.0:3000","manage:app"]
