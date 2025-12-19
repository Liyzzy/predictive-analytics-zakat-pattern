import os
import sqlite3

from werkzeug.security import generate_password_hash

DATABASE_PATH = "zakat_database.db"


def get_db_connection():
    """Get database connection with row factory for dict-like access."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """Initialize the SQLite database with required tables."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Users table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    """
    )

    # User profiles (financial data)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS user_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            age INTEGER,
            income REAL DEFAULT 0,
            savings REAL DEFAULT 0,
            gold_value REAL DEFAULT 0,
            investment_value REAL DEFAULT 0,
            family_size INTEGER DEFAULT 1,
            employment_status INTEGER DEFAULT 1,
            contribution_score INTEGER DEFAULT 50,
            haul_start_date DATE,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """
    )

    # Contribution history
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS contributions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            payment_date DATE NOT NULL,
            year INTEGER NOT NULL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """
    )

    # Donor data for admin analytics (migrated from CSV)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS donors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            donor_id TEXT UNIQUE NOT NULL,
            age INTEGER,
            income REAL,
            savings REAL,
            gold_value REAL,
            investment_value REAL,
            total_wealth REAL,
            family_size INTEGER,
            employment_status INTEGER,
            previous_contribution_score INTEGER,
            last_payment_date DATE,
            haul_start_date DATE,
            donor_tier TEXT,
            zakat_amount REAL
        )
    """
    )

    conn.commit()
    conn.close()
    print("Database initialized successfully!")


def seed_demo_users():
    """Create demo admin and user accounts."""
    conn = get_db_connection()
    cursor = conn.cursor()

    demo_users = [
        ("admin@zakatech.com", "admin123", "Admin User", "admin"),
        ("user@zakatech.com", "user123", "Demo Muzakki", "user"),
        ("ahmad@example.com", "password", "Ahmad bin Abdullah", "user"),
    ]

    for email, password, name, role in demo_users:
        try:
            password_hash = generate_password_hash(password)
            cursor.execute(
                """
                INSERT INTO users (email, password_hash, full_name, role)
                VALUES (?, ?, ?, ?)
            """,
                (email, password_hash, name, role),
            )

            # Create empty profile for users
            if role == "user":
                user_id = cursor.lastrowid
                cursor.execute(
                    """
                    INSERT INTO user_profiles (user_id, age, income, savings)
                    VALUES (?, 30, 0, 0)
                """,
                    (user_id,),
                )

        except sqlite3.IntegrityError:
            pass  # User already exists

    conn.commit()
    conn.close()
    print("Demo users created!")


def import_csv_to_sqlite():
    """Import existing CSV data into SQLite donors table."""
    import pandas as pd

    csv_path = "mock_zakat_data.csv"
    if not os.path.exists(csv_path):
        print("CSV file not found, skipping import.")
        return

    df = pd.read_csv(csv_path)
    conn = get_db_connection()
    cursor = conn.cursor()

    for _, row in df.iterrows():
        try:
            cursor.execute(
                """
                INSERT OR REPLACE INTO donors 
                (donor_id, age, income, savings, gold_value, investment_value, 
                 total_wealth, family_size, employment_status, previous_contribution_score,
                 last_payment_date, haul_start_date, donor_tier, zakat_amount)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    row["DonorID"],
                    row["Age"],
                    row["Income"],
                    row["Savings"],
                    row["GoldValue"],
                    row["InvestmentValue"],
                    row["TotalWealth"],
                    row["FamilySize"],
                    row["EmploymentStatus"],
                    row["PreviousContributionScore"],
                    row["LastPaymentDate"],
                    row["HaulStartDate"],
                    row["DonorTier"],
                    row["ZakatAmount"],
                ),
            )
        except Exception as e:
            print(f"Error importing row: {e}")

    conn.commit()
    conn.close()
    print(f"Imported {len(df)} donor records to SQLite!")


if __name__ == "__main__":
    init_database()
    seed_demo_users()
    import_csv_to_sqlite()
    print("\nDatabase setup complete!")
    print("Demo accounts:")
    print("  Admin: admin@zakatech.com / admin123")
    print("  User:  user@zakatech.com / user123")
