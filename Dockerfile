FROM python:3.11-slim

ENV PYTHONUNBUFFERED 1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

RUN mkdir /.fs /app
WORKDIR /app
VOLUME ["/.fs"]

RUN apt-get update -y && \
    apt-get install -y --no-install-recommends wait-for-it && \
    apt-get clean && \
    rm -vrf /var/lib/apt/lists/*

COPY requirements/ requirements/
RUN pip install -c requirements/constraints.txt -r requirements/prod.txt

COPY . .

COPY docker/wait_for_services.sh /usr/local/bin/wait_for_services.sh
COPY docker/entrypoint.sh /usr/local/bin/
ENTRYPOINT ["entrypoint.sh"]

EXPOSE 8000
CMD ["gunicorn", "digital_agenda.site.wsgi", "--bind", "0.0.0.0:8000"]
