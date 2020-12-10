FROM python:3.9-slim

WORKDIR /usr/src/app

ENV PGPASSFILE /opt/.pgpass

RUN mkdir /opt/areas
ENV AREA_ROOT /opt/areas

RUN touch .env

COPY requirements.txt requirements-server.txt ./

RUN pip install --no-cache-dir \
	-r requirements.txt \
	-r requirements-server.txt \
	&& find /usr/local/lib -path "*/*.pyo"  -delete \
	&& find /usr/local/lib -path "*/*.pyc"  -delete

COPY dp ./dp

HEALTHCHECK --start-period=5s \
	CMD test $(ps aux | grep -F 'python -m dp.server' | grep -v grep | wc -l) -lt 1

CMD ["python", "-m", "dp.server"]
