FROM apache/age:release_PG18_1.7.0

ENV POSTGRES_DB=micro \
    POSTGRES_USER=micro

COPY 10-initialize-micro.sql /docker-entrypoint-initdb.d/

