import json
import uuid
import os
import sqlite3

db_path = os.path.expanduser('~/Documents/ilmu komputer/semester 4/pkpl/elapo-developement/db.sqlite3')
connection = sqlite3.Connection(db_path)

def update():
    with open('customer.json', 'r') as file:
        customer_data = json.load(file)

    with open('cart.json', 'r') as file:
        cart_data = json.load(file)

    with open('review.json', 'r') as file:
        review_data = json.load(file)

    with open('fraudreport.json', 'r') as file:
        fraudreport_data = json.load(file)

    for customer  in customer_data:
        id = str(uuid.uuid4())
        for cart in cart_data:
            if cart['fields']['customer'] == customer['pk']:
                cart['fields']['customer'] = id
        for review in review_data:
            if review['fields']['customer'] == customer['pk']:
                review['fields']['customer']
        for fraudreport in fraudreport_data:
            if fraudreport['fields']['customer'] == customer['pk']:
                fraudreport['fields']['customer'] = id
        customer['pk'] = str(uuid.uuid4())


    with open('customer.json', 'w') as file:
        json.dump(customer_data, file)
    with open('cart.json', 'w') as file:
        json.dump(cart_data, file)
    with open('review.json', 'w') as file:
        json.dump(review_data, file)
    with open('fraudreport.json', 'w') as file:
        json.dump(fraudreport_data, file)
def generate_sql_insert_query():
    with open('customer.json', 'r') as file:
        customer_data = json.load(file)
        cursor = connection.cursor()
        for customer in customer_data:
            query = f"""
INSERT INTO main_customer (
id,
first_name,
last_name,
email,
nomor_hp,
domicile,
user_id
) VALUES (
'{customer['pk'].replace("-","")}', 
'{customer['fields']['first_name']}',
'{customer['fields']['last_name']}',
'{customer['fields']['email']}',
'{customer['fields']['nomor_hp']}',
'{customer['fields']['domicile']}',
{customer['fields']['user']}
);
            """
            cursor.execute(query)
    connection.commit()
    connection.close()
def generate_sql_insert_query_cart():
    with open('customer.json', 'r') as file:
        customer_data = json.load(file)
    with open('cart.json', 'r') as file:
        cart_data = json.load(file)
        cursor = connection.cursor()
        for cart in cart_data:
            
            query = f'''INSERT INTO "cart_cart" ("id", "customer_id", "is_checked_out", "created_at")
        VALUES ('{str(cart['pk']).replace('-','')}', '{str(cart['fields']['customer']).replace('-','')}', {cart['fields']['is_checked_out']}, '{cart['fields']['created_at']}')'''
            cursor.execute(query)
        connection.commit()
        connection.close()

def generate_sql_insert_query_review():
    with open('review.json', 'r') as file:
        review_data = json.load(file)

        cursor = connection.cursor()
        for review in review_data:
            query = f'''
                INSERT INTO "review_review" ("review_id", "description", "rating", "customer_id", "order_id")
                VALUES ('{review['pk']}', '{review['fields']['description']}', {review['fields']['rating']}, '{review['fields']['customer']}', '{review['fields']['order']}');
            '''
            cursor.execute(query)
        connection.commit()
        connection.close()
def update_admin_id_to_uuid():
    cursor = connection.cursor()
    cursor.execute("select * from main_admin")
    pair_admins = []
    admins = cursor.fetchall()
    for admin in admins:
        pair = (admin, uuid.uuid4()) 
        pair_admins.append(pair)
    cursor.execute("select * from administrator_adminactivitylog")
    print(pair_admins)
    data = []
    adminlog = cursor.fetchall()
    for log in adminlog:
        for pair in pair_admins:
            if log[3] == pair[0][0]:
                temp_log = log
                temp_log = list(temp_log)
                temp_log[0] = str(uuid.uuid4()).replace("-", "")
                temp_log[3] = str(pair[1]).replace("-", "")
                data.append(tuple(temp_log))
    print(data)
    data2 = []
    for pair in pair_admins:
        temp_admin = pair[0]
        temp_admin = list(temp_admin)
        temp_admin[0] = str(pair[1]).replace("-", "")
        data2.append(tuple(temp_admin))
    print(data2)
    cursor.execute("ALTER TABLE administrator_adminactivitylog RENAME TO administrator_adminactivitylog_old")
    insert_query = '''CREATE TABLE IF NOT EXISTS "administrator_adminactivitylog" ("id" char(32) NOT NULL PRIMARY KEY, "action" text NOT NULL, "timestamp" datetime NOT NULL, "admin_id" char(32) NOT NULL REFERENCES "main_admin" ("id") DEFERRABLE INITIALLY DEFERRED);'''
    cursor.execute(insert_query)
    cursor.execute("ALTER TABLE main_admin RENAME TO main_admin_old")
    insert_query = '''CREATE TABLE IF NOT EXISTS "main_admin" (
    "id" char(32) NOT NULL PRIMARY KEY,
    "first_name" varchar(25) NOT NULL,
    "last_name" varchar(25) NOT NULL,
    "nomor_hp" varchar(16) NOT NULL,
    "email" varchar(50) NOT NULL,
    "user_id" integer NOT NULL UNIQUE REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED
);'''
    cursor.execute(insert_query)
    for d in data2:
        query = f'''
        INSERT INTO main_admin (first_name, last_name, nomor_hp, email, user_id)
        values
            ('{d[0]}', '{d[1]}', '{d[2]}', '{d[3]}', '{d[4]}', {d[5]})
        ;'''
    for d in data:
        query = f'''
        INSERT INTO administrator_adminactivitylog (id, action, timestamp, admin_id)
        values 
            ('{d[0]}', '{d[1]}', '{d[2]}', '{d[3]}')
        '''
update_admin_id_to_uuid()
