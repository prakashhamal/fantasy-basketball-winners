FROM python:alpine3.6
MAINTAINER prakashhamal@gmail.com


# We copy just the requirements.txt first to leverage Docker cache
COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip install -r requirements.txt

COPY . /app

ENTRYPOINT [ "python"]
cmd [ "app.py" ]
