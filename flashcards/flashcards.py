import sqlite3
from datetime import datetime, timedelta
import os

current_dir = os.path.dirname(os.path.realpath(__file__))
db_path = os.path.join(current_dir, 'flashcards.db')
# Global variable to keep track of the simulated date
simulated_date = datetime.now().date()

def advance_date(days=1):
    global simulated_date  # Declare simulated_date as global to modify it
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Fetch the current simulated date from the database
    cursor.execute('SELECT current_date FROM simulated_time WHERE id = 1')
    row = cursor.fetchone()
    if row:
        simulated_date = datetime.strptime(row[0], '%Y-%m-%d').date()
    else:
        # If there's no entry in the database, we should probably insert the current simulated date
        simulated_date = datetime.now().date()
        cursor.execute('INSERT INTO simulated_time (id, current_date) VALUES (1, ?)', (simulated_date,))

    # Calculate the new simulated date
    new_date = simulated_date + timedelta(days=days)

    # Update the simulated date in the database and the global variable
    cursor.execute('UPDATE simulated_time SET current_date = ? WHERE id = 1', (new_date,))
    simulated_date = new_date  # Update the global variable

    conn.commit()
    conn.close()

    return new_date


def get_simulated_date():
    """
    Returns the current simulated date from the database.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Fetch the current simulated date from the database
    cursor.execute('SELECT current_date FROM simulated_time WHERE id = 1')
    row = cursor.fetchone()
    conn.close()

    # If the row is found, return the date, otherwise return the current date
    if row:
        return datetime.strptime(row[0], '%Y-%m-%d').date()
    else:
        # If there's no entry in the database, we should probably create it
        return advance_date(0)

# Connect to the SQLite database. If it does not exist, it will be created.
current_dir = os.path.dirname(os.path.realpath(__file__))

def initialize_database():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create table for flashcards if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS flashcards (
        id INTEGER PRIMARY KEY,
        front TEXT NOT NULL,
        back TEXT NOT NULL,
        created_at DATE NOT NULL
    )
    ''')

    # Create table for review_schedule if it doesn't exist
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

    # Create table for simulated_time if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS simulated_time (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        current_date DATE NOT NULL
    )
    ''')

    # Check if the simulated_time table is empty and insert the current date if it is
    cursor.execute('SELECT EXISTS(SELECT 1 FROM simulated_time WHERE id = 1)')
    if not cursor.fetchone()[0]:
        real_date = datetime.now().date()
        cursor.execute('INSERT INTO simulated_time (id, current_date) VALUES (1, ?)', (real_date,))

    # Commit the changes and close the connection
    conn.commit()
    conn.close()

# Call this function at the start of your application to ensure the database is initialized
initialize_database()


# def add_flashcard(front, back):
#     current_dir = os.path.dirname(os.path.realpath(__file__))

#     # Construct the path to the database file within the current directory
#     db_path = os.path.join(current_dir, 'flashcards.db')

#     # Connect to the SQLite database using the path
#     conn = sqlite3.connect(db_path)
#     cursor = conn.cursor()

#     # Insert the new flashcard into the flashcards table
#     cursor.execute('INSERT INTO flashcards (front, back) VALUES (?, ?)', (front, back))
#     card_id = cursor.lastrowid

#     # Set the next review date to today for the new flashcard
#     next_review = datetime.now().date()
    
#     # Insert the initial review schedule for the new flashcard
#     cursor.execute('INSERT INTO review_schedule (card_id, next_review, interval) VALUES (?, ?, ?)',
#                    (card_id, next_review, 1))
    
#     # Commit the changes and close the connection
#     conn.commit()
#     conn.close()

#     return f"Flashcard with id {card_id} added successfully."

def review_flashcard(card_id, user_input):
    # Connect to the SQLite database using the path
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get the current simulated date from the database
    cursor.execute('SELECT current_date FROM simulated_time WHERE id = 1')
    row = cursor.fetchone()
    simulated_date = row[0] if row else datetime.now().date()

    # If the card is not found, return an error message
    if row is None:
        return f"Flashcard with id {card_id} not found."

    current_interval, review_count, success_count = row
    print(f"Current interval: {current_interval}, Review Count: {review_count}, Success Count: {success_count}")

    # Determine the new interval and update the success count based on the user's input
    if user_input.lower() == 'yes':
        new_interval = current_interval * 2
        success_count += 1  # Increment the success count
    else:
        new_interval = 1
        # Do not increment the success count if the user did not remember the flashcard

    # Increment the review count since the flashcard is being reviewed
    review_count += 1

    # Calculate the next review date based on the new interval
    next_review = simulated_date + timedelta(days=new_interval)
    print(f"Next review date: {next_review}")

    # Update the review schedule with the new interval, next review date, last_reviewed date, review count, and success count
    cursor.execute('''
    UPDATE review_schedule
    SET next_review = ?, interval = ?, last_reviewed = ?, review_count = ?, success_count = ?
    WHERE card_id = ?''', (next_review, new_interval, simulated_date, review_count, success_count, card_id))

    # Commit the changes and close the connection
    conn.commit()
    conn.close()

    return f"Flashcard with id {card_id} reviewed. Next review is in {new_interval} days."


def get_due_flashcards():
    # Connect to the SQLite database using the path
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get the current simulated date from the database
    cursor.execute('SELECT current_date FROM simulated_time WHERE id = 1')
    row = cursor.fetchone()
    simulated_date = row[0] if row else datetime.now().date()

    # Get all flashcards that are due for review (where the next review date is today or in the past)
    cursor.execute('SELECT flashcards.id, front, back FROM flashcards JOIN review_schedule ON flashcards.id = review_schedule.card_id WHERE next_review <= ?', (simulated_date,))
    due_flashcards = cursor.fetchall()

    # Close the connection to the database
    conn.close()

    return due_flashcards


def delete_all_flashcards_and_reset_date():
    # Connect to the SQLite database using the path
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Delete all records from the review_schedule table
    cursor.execute('DELETE FROM review_schedule')

    # Delete all records from the flashcards table
    cursor.execute('DELETE FROM flashcards')

    # Reset the simulated date to the current real date
    real_date = datetime.now().date()
    cursor.execute('UPDATE simulated_time SET current_date = ? WHERE id = 1', (real_date,))

    # Commit the changes and close the connection
    conn.commit()
    conn.close()

    return "All flashcards and their review schedules have been deleted and the date has been reset."



# Function to add flashcard with automatic timestamp for creation
def add_flashcard_with_timestamp(front, back):
    # Use global simulated_date instead of calling datetime.now().date()
    global simulated_date
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO flashcards (front, back, created_at) VALUES (?, ?, ?)', (front, back, simulated_date))
    card_id = cursor.lastrowid
    cursor.execute('INSERT INTO review_schedule (card_id, next_review) VALUES (?, ?)', (card_id, simulated_date))
    conn.commit()
    conn.close()
    return f"Flashcard with id {card_id} added successfully."


# Function to print flashcard statistics
def print_flashcard_statistics():
    # Connect to the SQLite database using the path
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # Get all flashcards with their review schedule and calculate age in days
    cursor.execute('''
    SELECT flashcards.id, front, back, created_at, last_reviewed, next_review, interval, review_count, success_count,
           (julianday(?) - julianday(created_at)) AS age
    FROM flashcards
    JOIN review_schedule ON flashcards.id = review_schedule.card_id
    ''', (simulated_date,))
    flashcards_info = cursor.fetchall()
    conn.close()

    # Print out the statistics for each flashcard
    print("ID".ljust(5) + "Front".ljust(30) + "Back".ljust(30) +
          "Created (Age)".ljust(20) + "Last Reviewed".ljust(15) +
          "Next Review".ljust(15) + "Interval (days)".ljust(17) +
          "Review Count".ljust(14) + "Success Count".ljust(15))
    print("-" * 150)

    for card in flashcards_info:
        print(str(card[0]).ljust(5) +
              card[1][:25].ljust(30) +
              card[2][:25].ljust(30) +
              (str(card[3]) + " (" + str(int(card[8])) + " days)").ljust(20) +
              (str(card[4]) if card[4] else "N/A").ljust(15) +
              str(card[5]).ljust(15) +
              str(card[6]).ljust(17) +
              str(card[7]).ljust(14) +
              str(card[8]).ljust(15))
        print("-" * 150)

delete_all_flashcards_and_reset_date()

# Add some new flashcards
add_flashcard_with_timestamp("Capital of France", "Paris")
add_flashcard_with_timestamp("Largest ocean on Earth", "Pacific")
add_flashcard_with_timestamp("The chemical symbol for Gold", "Au")

# Print flashcard statistics
# print_flashcard_statistics()

# due_flashcards = get_due_flashcards()
# print(due_flashcards)

# advance_date()
# print(get_simulated_date())
# print_flashcard_statistics()

# print("Current simulated date:", get_simulated_date())
# # Execute and print SQL query: SELECT card_id, next_review FROM review_schedule

# advance_date(1)  # Advance the date by one day
# print("Advanced simulated date:", get_simulated_date())
# # Execute and print SQL query: SELECT card_id, next_review FROM review_schedule

# due_flashcards = get_due_flashcards()
# print("Due flashcards:", due_flashcards)

# review_flashcard()

def main_menu():
    while True:
        print("\nFlashcard Review System")
        print("1 - Review due flashcards")
        print("2 - Print flashcard statistics")
        print("3 - Exit")
        choice = input("Enter your choice: ")

        if choice == "1":
            due_flashcards = get_due_flashcards()
            if due_flashcards:
                print("\nDue flashcards for review:")
                for card in due_flashcards:
                    card_id, front, back = card
                    print(f"Flashcard ID: {card_id}, Front: {front}, Back: {back}")
                    user_input = input("Did you remember this flashcard? (yes/no): ")
                    review_flashcard(card_id, user_input)
            else:
                print("\nNo flashcards are due for review today.")
                print("\nArtificially advancing the schedule by one day.")
                advance_date()
        elif choice == "2":
            print("\nFlashcard Statistics:")
            print_flashcard_statistics()
        elif choice == "3":
            print("Exiting the program.")
            break
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")

if __name__ == "__main__":
    main_menu()
