#!/bin/bash
if [ ! -s "$PGDATA/PG_VERSION" ]; then
echo "*:*:*:$PG_REP_USER:$PG_REP_PASSWORD" > ~/.pgpass
chmod 0600 ~/.pgpass
until ping -c 1 -W 1 db_image
do
echo "Waiting for master to ping..."
sleep 1s
done
until pg_basebackup --pgdata=/var/lib/postgresql/data -R --slot=replication_slot --host=db_image --port=5432
do
echo "Waiting for master to connect..."
sleep 1s
done
echo "host replication all 0.0.0.0/0 md5" >> "$PGDATA/pg_hba.conf"
set -e
chown postgres. ${PGDATA} -R
chmod 700 ${PGDATA} -R
fi
sed -i 's/wal_level = hot_standby/wal_level = replica/g' ${PGDATA}/postgresql.conf
exec "$@"