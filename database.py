import sqlite3

def create_database():
    conn = sqlite3.connect("business.db")
    cursor = conn.cursor()

    # Customers table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY,
            name TEXT,
            email TEXT,
            city TEXT
        )
    """)

    # Orders table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY,
            customer_id INTEGER,
            product TEXT,
            amount REAL,
            status TEXT,
            date TEXT
        )
    """)

    # Sample data
    cursor.executemany("INSERT OR IGNORE INTO customers VALUES (?,?,?,?)", [
        (1, "Maria Lopez", "maria@email.com", "Buenos Aires"),
        (2, "Carlos Perez", "carlos@email.com", "Cordoba"),
        (3, "Ana Garcia", "ana@email.com", "Rosario"),
        (4, "Juan Martinez", "juan@email.com", "Mendoza"),
    ])

    cursor.executemany("INSERT OR IGNORE INTO orders VALUES (?,?,?,?,?,?)", [
        (1, 1, "Laptop", 1200.00, "Delivered", "2024-01-15"),
        (2, 1, "Mouse", 25.00, "Delivered", "2024-01-20"),
        (3, 2, "Monitor", 350.00, "Processing", "2024-02-01"),
        (4, 3, "Keyboard", 80.00, "Shipped", "2024-02-10"),
        (5, 4, "Headphones", 150.00, "Delivered", "2024-02-15"),
        (6, 2, "Webcam", 95.00, "Processing", "2024-03-01"),
    ])

    conn.commit()
    conn.close()
    print("Database created successfully!")

if __name__ == "__main__":
    create_database()

