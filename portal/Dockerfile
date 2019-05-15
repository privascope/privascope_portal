FROM billyteves/ubuntu-dind:16.04
# https://github.com/billyteves/ubuntu-dind

ENV PYTHON_VERSION 3.7

# Merge Python on top of Ubuntu-Docker:
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt-get update
RUN apt-get install -y build-essential python${PYTHON_VERSION}
RUN wget https://bootstrap.pypa.io/get-pip.py
RUN python${PYTHON_VERSION} get-pip.py

# This app:

# Prereqs for PySAML
RUN apt-get install -y xmlsec1 libffi-dev libssl-dev

ENV PYTHONUNBUFFERED 1

EXPOSE 8000

RUN mkdir /usr/src/app
WORKDIR /usr/src/app

RUN pip3 install psycopg2-binary django-extensions

COPY requirements.txt /tmp
RUN pip3 install -r /tmp/requirements.txt

COPY . /usr/src/app/

CMD python${PYTHON_VERSION} manage.py runserver 0.0.0.0:8000
