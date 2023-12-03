import os
import psycopg2
from psycopg2 import sql
from datetime import datetime, timedelta

# Function to get database connection
def get_db_connection():
    return psycopg2.connect(
        dbname='postgres',
        user='postgres',
        password='tyD6mWeWgpd9eWaj',
        host='db.nxcepjywkwnwvafzjjzb.supabase.co',
        port='5432'
    )

# Function to advance simulated date
def advance_date(days=1):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT current_date FROM simulated_time WHERE id = 1')
    row = cursor.fetchone()

    if row:
        simulated_date = row[0]
    else:
        simulated_date = datetime.now().date()
        cursor.execute(
            'INSERT INTO simulated_time (id, current_date) VALUES (1, %s)',
            (simulated_date,)
        )
    
    new_date = simulated_date + timedelta(days=days)
    cursor.execute(
        'UPDATE simulated_time SET current_date = %s WHERE id = 1',
        (new_date,)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return new_date

# Function to get the current simulated date
def get_simulated_date():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT current_date FROM simulated_time WHERE id = 1')
    row = cursor.fetchone()
    conn.close()

    if row:
        return row[0]
    else:
        return advance_date(0)

# Function to initialize the database
def initialize_database():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create tables if they do not exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS flashcards (
        id SERIAL PRIMARY KEY,
        front TEXT NOT NULL,
        back TEXT NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS review_schedule (
        card_id INTEGER NOT NULL,
        next_review DATE NOT NULL,
        interval INTEGER NOT NULL DEFAULT 1,
        last_reviewed DATE,
        review_count INTEGER NOT NULL DEFAULT 0,
        success_count INTEGER NOT NULL DEFAULT 0,
        FOREIGN KEY(card_id) REFERENCES flashcards(id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS simulated_time (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        current_date DATE NOT NULL
    )
    ''')

    cursor.execute('SELECT EXISTS(SELECT 1 FROM simulated_time WHERE id = 1)')
    if not cursor.fetchone()[0]:
        cursor.execute(
            'INSERT INTO simulated_time (id, current_date) VALUES (1, %s)',
            (datetime.now().date(),)
        )

    conn.commit()
    cursor.close()
    conn.close()

# Function to add a flashcard with an automatic timestamp
def add_flashcard_with_timestamp(front, back):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO flashcards (front, back, created_at) VALUES (%s, %s, %s) RETURNING id',
        (front, back, datetime.now())
    )
    card_id = cursor.fetchone()[0]
    cursor.execute(
        'INSERT INTO review_schedule (card_id, next_review) VALUES (%s, %s)',
        (card_id, datetime.now().date())
    )
    conn.commit()
    cursor.close()
    conn.close()
    return f"Flashcard with id {card_id} added successfully."

# Function to review a flashcard
def review_flashcard(card_id, user_input):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT current_date FROM simulated_time WHERE id = 1')
    simulated_date = cursor.fetchone()[0]

    cursor.execute(
        'SELECT interval, review_count, success_count FROM review_schedule WHERE card_id = %s',
        (card_id,)
    )
    row = cursor.fetchone()

    if row is None:
        cursor.close()
        conn.close()
        return f"Flashcard with id {card_id} not found."

    current_interval, review_count, success_count = row

    new_interval = current_interval * 2 if user_input.lower() == 'yes' else 1
    success_count += 1 if user_input.lower() == 'yes' else success_count
    review_count += 1

    next_review = simulated_date + timedelta(days=new_interval)

    cursor.execute(
        '''
        UPDATE review_schedule
        SET next_review = %s, interval = %s, last_reviewed = %s, review_count = %s, success_count = %s
        WHERE card_id = %s
        ''',
        (next_review, new_interval, simulated_date, review_count, success_count, card_id)
    )

    conn.commit()
    cursor.close()
    conn.close()
    return f"Flashcard with id {card_id} reviewed. Next review is in {new_interval} days."

# Function to get due flashcards
def get_due_flashcards():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT current_date FROM simulated_time WHERE id = 1')
    simulated_date = cursor.fetchone()[0]

    cursor.execute(
        '''
        SELECT flashcards.id, front, back
        FROM flashcards
        JOIN review_schedule ON flashcards.id = review_schedule.card_id
        WHERE next_review <= %s
        ''',
        (simulated_date,)
    )
    due_flashcards = cursor.fetchall()
    cursor.close()
    conn.close()
    return due_flashcards

# Function to delete all flashcards and reset date
def delete_all_flashcards_and_reset_date():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM review_schedule')
    cursor.execute('DELETE FROM flashcards')
    cursor.execute('UPDATE simulated_time SET current_date = %s WHERE id = 1', (datetime.now().date(),))
    conn.commit()
    cursor.close()
    conn.close()
    return "All flashcards and their review schedules have been deleted and the date has been reset."

# Function to print flashcard statistics
def print_flashcard_statistics():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        '''
        SELECT flashcards.id, front, back, created_at, last_reviewed, next_review, interval, review_count, success_count,
               (CURRENT_DATE - created_at) AS age
        FROM flashcards
        JOIN review_schedule ON flashcards.id = review_schedule.card_id
        '''
    )
    flashcards_info = cursor.fetchall()
    cursor.close()
    conn.close()

    # Your code to print the flashcard statistics goes here
    # ...

# Initialization and example usage
initialize_database()
add_flashcard_with_timestamp("Capital of France", "Paris")
add_flashcard_with_timestamp("Largest ocean on Earth", "Pacific")
add_flashcard_with_timestamp("The chemical symbol for Gold", "Au")
