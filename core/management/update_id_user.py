import json
import uuid
import os
import sqlite3

db_path = os.path.expanduser('~/Documents/ilmu komputer/semester 4/pkpl/elapo-developement/db.sqlite3')
connection = sqlite3.Connection(db_path)

def update_worker():
    pass
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
generate_sql_insert_query_cart()
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

