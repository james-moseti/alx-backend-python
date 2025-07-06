import seed
from decimal import Decimal

# Fetch one Page
def paginate_users(page_size, offset):
    """
    Fetch a single page of users using LIMIT and OFFSET.
    """
    conn = seed.connect_to_prodev()
    cursor = conn.cursor(dictionary=True)

    query = "SELECT * FROM user_data LIMIT %s OFFSET %s"
    cursor.execute(query, (page_size, offset))
    rows = cursor.fetchall()

    cursor.close()
    conn.close()
    return rows

# Generator Function: Lazy Pagination
def lazy_paginate(page_size):
    """
    Generator that lazily fetches and yields paginated users.
    Only fetches the next page when needed.
    """
    offset = 0
    while True:
        page = paginate_users(page_size, offset)
        if not page:
            break
        for user in page:
            yield user
        offset += page_size

# Usage
if __name__ == '__main__':
    print("Paginated users (lazy load):")
    for user in lazy_paginate(page_size=10):
        print(user)
