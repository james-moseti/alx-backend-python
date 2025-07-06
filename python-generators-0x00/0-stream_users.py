import seed
from itertools import islice

def stream_users():
    db_connection = seed.connect_to_prodev()
    cursor = db_connection.cursor(dictionary=True)
    cursor.execute(f"SELECT * FROM {seed.TABLE_NAME}")
    
    for row in cursor:
        yield row
    
    cursor.close()
    db_connection.close()

for user in islice(stream_users(), 10):
    print(user)