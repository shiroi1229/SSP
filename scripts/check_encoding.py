import psycopg2
conn=psycopg2.connect(host='172.25.208.1', port=5432, dbname='ssp_memory', user='ssp_admin', password='Mizuho0824')
print(conn.encoding)
