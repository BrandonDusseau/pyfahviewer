FROM python:3.8

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN pip install --upgrade pip

COPY requirements.txt ./

RUN pip install -r requirements.txt

CMD ["gunicorn", "-b", "0.0.0.0:5000", "-w", "1", "wsgi:app"]
