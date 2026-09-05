import duckdb
conn = duckdb.connect("data/knowledge_base.duckdb")
print(conn.execute("SHOW TABLES").fetchall())
