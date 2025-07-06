import seed

def stream_user_ages():
    """
    Generator that yields user ages one by one from the user_data table.
    """
    conn = seed.connect_to_prodev()
    cursor = conn.cursor()
    cursor.execute("SELECT age FROM user_data")

    for (age,) in cursor:  
        yield float(age)

    cursor.close()
    conn.close()


def compute_average_age():
    """
    Computes and prints the average age using the stream_user_ages generator.
    """
    total = 0
    count = 0

    for age in stream_user_ages(): 
        total += age
        count += 1

    if count == 0:
        print("Average age of users: 0")
    else:
        avg = total / count
        print(f"Average age of users: {avg:.2f}")


if __name__ == "__main__":
    compute_average_age()
