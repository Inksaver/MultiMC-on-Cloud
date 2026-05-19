import sqlite3
from sqlite3 import Error
conn = None
cursor = None

def find_row(name):
    ''' find record from name field '''
    cursor.execute(f"SELECT id, name, javaWindows, javaLinux FROM game WHERE name = '{name}'")# get record of matching game
    return cursor.fetchall()		    

def update_row(row_id, field, value):
    ''' update record usind given row id '''
    update_statement = f'UPDATE game SET {field}=? WHERE id = ?'
    cursor.execute(update_statement,(value, row_id))
    conn.commit()

def insert_row(table_name, fields, data):
    ''' insert a new record '''
    field_names = ""
    data_values = ""
    for field in fields:
        field_names += f"{field},"
    field_names = field_names[:-1]

    for field in data:
        if type(field) is str:
            modified = field.replace("'", "`")
            data_values += f"'{modified}',"
        else:
            data_values += f"{field},"
    data_values = data_values[:-1]	

    sqlite_insert_query = f"""INSERT INTO {table_name} ({field_names}) VALUES ({data_values})"""
    # print(sqlite_insert_query)
    cursor.execute(sqlite_insert_query)	
    conn.commit()
    
    return cursor.lastrowid

def open(db_file):
    ''' attempt to open a database file '''
    global conn, cursor
    try:
        with sqlite3.connect(db_file) as conn:
            cursor = conn.cursor()
            #print(f"Opened SQLite database with version {sqlite3.sqlite_version} successfully.")
            return conn, cursor

    except sqlite3.OperationalError as e:
        print(f"Failed to open database {db_file}: {e}")	
        return None

def create(db_file):
    ''' Create a sqlite database with the file name in db_file '''
    global conn, cursor
    
    sql_statement = """CREATE TABLE IF NOT EXISTS game (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    javaWindows TEXT,
    javaLinux TEXT
    );"""

    with sqlite3.connect(db_file) as conn:		# create a database connection
        cursor = conn.cursor()				# create a cursor
        # execute statements
        #for statement in sql_statements:
        cursor.execute(sql_statement)
        conn.commit()					# commit the change
        
    # add multimc.cfg javaPath
    insert_row("game", ["name", "javaWindows", "javaLinux"], ["multimc.cfg","",""])