import asyncio
import aiosqlite
import sqlite3

async def setup_database():
    """Setup sample database with users table."""
    async with aiosqlite.connect("example.db") as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                name TEXT,
                age INTEGER
            )
        """)
        
        # Insert sample data
        users = [
            ("Alice", 28),
            ("Bob", 35),
            ("Charlie", 42),
            ("Diana", 31),
            ("Eve", 45),
            ("Frank", 38),
            ("Grace", 50)
        ]
        
        await db.executemany("INSERT OR IGNORE INTO users (name, age) VALUES (?, ?)", users)
        await db.commit()
        print("Database setup complete")

async def async_fetch_users():
    """Fetch all users from the database."""
    async with aiosqlite.connect("example.db") as db:
        cursor = await db.execute("SELECT * FROM users")
        users = await cursor.fetchall()
        print(f"All users: {users}")
        return users

async def async_fetch_older_users():
    """Fetch users older than 40."""
    async with aiosqlite.connect("example.db") as db:
        cursor = await db.execute("SELECT * FROM users WHERE age > ?", (40,))
        older_users = await cursor.fetchall()
        print(f"Users older than 40: {older_users}")
        return older_users

async def fetch_concurrently():
    """Execute both queries concurrently using asyncio.gather."""
    print("Starting concurrent database queries...")
    
    # Run both queries concurrently
    all_users, older_users = await asyncio.gather(
        async_fetch_users(),
        async_fetch_older_users()
    )
    
    print(f"\nResults:")
    print(f"Total users found: {len(all_users)}")
    print(f"Users older than 40: {len(older_users)}")
    
    return all_users, older_users

# Main execution
async def main():
    await setup_database()
    await fetch_concurrently()

if __name__ == "__main__":
    asyncio.run(main())