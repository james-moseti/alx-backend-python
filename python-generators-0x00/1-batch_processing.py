import seed

def stream_users_in_batches(batch_size):
    """
    Generator that yields batches of users from user_data table.
    Each batch is a list of dictionaries.
    """
    conn = seed.connect_to_prodev()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(f"SELECT * FROM {seed.TABLE_NAME}")

    batch = []
    for row in cursor:
        batch.append(row)
        if len(batch) == batch_size:
            yield batch
            batch = []

    if batch:
        yield batch

    cursor.close()
    conn.close()


def batch_processing(batch_size):
    """
    Generator that yields users over age 25 from each batch.
    """
    for batch in stream_users_in_batches(batch_size): 
        for user in batch:
            if user['age'] > 25:
                yield user


if __name__ == "__main__":
    from itertools import islice

    for user in islice(batch_processing(5), 10):
        print(user)
