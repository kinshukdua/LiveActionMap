FROM python:3.10-slim@sha256:2bac43769ace90ebd3ad83e5392295e25dfc58e58543d3ab326c3330b505283d


WORKDIR /app
COPY requirements.txt .
RUN pip3 install -r requirements.txt
RUN python3 -m spacy download en

COPY . .

CMD [ "python", "scrape.py" ]
