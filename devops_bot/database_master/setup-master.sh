#!/bin/bash

echo "host replication all 0.0.0.0/0 md5" >> "$PGDATA/pg_hba.conf"
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL

CREATE USER $PG_REP_USER REPLICATION LOGIN CONNECTION LIMIT 100 ENCRYPTED PASSWORD '$PG_REP_PASSWORD';
select pg_create_physical_replication_slot('replication_slot');

EOSQL

mkdir /var/lib/postgresql/data/archive
chown postgres. ${PGDATA} -R
chmod 700 ${PGDATA} -R
cat >> ${PGDATA}/postgresql.conf <<-EOF
log_statement=all
logging_collector=on
log_directory = '/var/log/postgresql' 
log_filename = 'postgresql.log' 
log_replication_commands = on
log_line_prefix = '%m [%p] %u '
archive_mode = on
archive_command = 'cp %p /var/lib/postgresql/data/archive/%f' 
max_wal_senders = 10
wal_level = replica                     
wal_log_hints = on
EOF