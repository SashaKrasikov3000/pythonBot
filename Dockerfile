FROM python:3.13.0a4-slim-bullseye
RUN mkdir /home/app
WORKDIR /home/app
COPY . .
RUN pip install -r requirements.txt
RUN python setup_db.py

CMD ["python", "main.py"]