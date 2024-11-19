FROM python:3.10
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

RUN apt-get update

WORKDIR /hxat
COPY ./hxat/requirements/base.txt ./requirements.txt
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . .
RUN chmod +x ./wait-for-it.sh ./docker_entrypoint.sh
ENTRYPOINT ["./wait-for-it.sh", "db:5432", "--", "./docker_entrypoint.sh"]
