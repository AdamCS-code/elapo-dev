import uuid
import sqlite3

conn = sqlite3.connect('db.sqlite3')
def update_customer():
    # create new table, rename previous one with suffix _old
    cursor = conn.cursor()

    cursor.execute('''
        ALTER TABLE main_customer RENAME TO main_customer_old
    ''')

    

    pass

def update_worker():
    pass
