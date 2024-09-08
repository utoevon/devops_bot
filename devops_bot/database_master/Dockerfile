FROM postgres:14-alpine
COPY ./setup-master.sh /docker-entrypoint-initdb.d/setup-master.sh
RUN mkdir /var/log/postgresql
RUN touch /var/log/postgresqlpostgresql.log
RUN chmod -R 777 /var/log/postgresql
RUN chmod 0666 /docker-entrypoint-initdb.d/setup-master.sh