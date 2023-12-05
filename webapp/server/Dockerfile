FROM python:3

WORKDIR /server

ENV FLASK_APP=server.py
ENV FLASK_DEBUG=1

COPY ./requirements.txt .

RUN pip install -r requirements.txt

COPY . .

CMD [ "python", "server.py" ]