FROM python:3.12

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN python -m pip install --upgrade pip

COPY requirements.txt ./

RUN python -m pip install -r requirements.txt

COPY . .

CMD ["gunicorn", "-b", "0.0.0.0:5001", "-w", "1", "wsgi:app"]
