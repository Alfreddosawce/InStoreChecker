import sqlite3

# create a connection/connect to the database, it will create the file example.db if it doesnt exist
conn = sqlite3.connect("example.db")

#create a cursor to run SQL commmands, this is what you use to run SQL commands
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        tcin TEXT PRIMARY KEY,
        title TEXT
    )
    """)

# if we create table everytime, does that mean the program runs and creates a new database everytime it starts up?

conn.commit() #saves your changes
conn.close() #finishes the session

#entering fake product

conn = sqlite3.connect("example.db")
cursor = conn.cursor()

cursor.execute("INSERT INTO products (tcin, title) VALUES (?, ?)", ("12345678", "Cool Blender"))
conn.commit()
conn.close()

conn = sqlite3.connect("example.db")
cursor = conn.cursor()

cursor.execute("SELECT * FROM products")
rows = cursor.fetchall()

for row in rows:
    print(row)
    conn.close()
    
