FROM python:3-slim

ENV LANG=C.UTF-8 \
    PYTHONUNBUFFERED=1

RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -Ur /requirements.txt

COPY . /attachments

WORKDIR /attachments

CMD ["python", "manage.py", "test"]
