FROM rust:1.50-buster AS builder

WORKDIR /usr/src/reports

COPY ./Cargo.toml ./
COPY ./Cargo.lock ./
COPY ./reports ./reports
COPY ./src ./src
COPY ./formatter ./formatter

RUN cargo build --release --bin dp-report

FROM python:3.9-slim-buster

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

COPY docker-install-packages.sh ./docker-install-packages.sh
RUN bash ./docker-install-packages.sh

COPY docker-healthcheck.sh ./docker-healthcheck.sh

ENV DP_REPORT_BIN /opt/dp-report
COPY --from=builder /usr/src/reports/target/release/dp-report /opt/dp-report

HEALTHCHECK --start-period=5s \
	CMD bash ./docker-healthcheck.sh

CMD ["python", "-m", "dp.server"]
