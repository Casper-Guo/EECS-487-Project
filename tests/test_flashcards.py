# test_flashcards.py

import pytest
from flashcards.flashcards import (advance_date, add_flashcard_with_timestamp, review_flashcard,
                                   get_due_flashcards, delete_all_flashcards, simulated_date)
from datetime import timedelta
import sqlite3

# or
from flashcards import db_path  # If importing from another package



@pytest.fixture
def setup_database():
    delete_all_flashcards()
    # Add test data to the database
    add_flashcard_with_timestamp("Capital of France", "Paris")
    add_flashcard_with_timestamp("Largest ocean on Earth", "Pacific")
    # The fixture returns the ids of the new flashcards
    return [1, 2]

def test_advance_date():
    original_date = simulated_date
    advance_date(1)
    assert simulated_date == original_date + timedelta(days=1), "Date should advance by 1 day"

def test_add_flashcard_with_timestamp(setup_database):
    # setup_database is used to reset the environment before running the test
    card_ids = setup_database
    for card_id in card_ids:
        # Test that each card has the correct created_at date
        # (You would need to implement a function to retrieve a flashcard by id)
        flashcard = get_flashcard_by_id(card_id)
        assert flashcard['created_at'] == simulated_date, "Flashcard timestamp should match simulated date"

def test_review_flashcard_yes(setup_database):
    card_id = setup_database[0]
    review_flashcard(card_id, 'yes')
    # (You would need to implement a function to retrieve review information by flashcard id)
    review_info = get_review_info_by_card_id(card_id)
    assert review_info['interval'] > 1, "Interval should increase after a positive review"

def test_review_flashcard_no(setup_database):
    card_id = setup_database[0]
    review_flashcard(card_id, 'no')
    review_info = get_review_info_by_card_id(card_id)
    assert review_info['interval'] == 1, "Interval should reset after a negative review"

def test_get_due_flashcards(setup_database):
    due_flashcards = get_due_flashcards()
    assert len(due_flashcards) == len(setup_database), "All flashcards should initially be due"

def test_delete_all_flashcards(setup_database):
    delete_all_flashcards()
    due_flashcards = get_due_flashcards()
    assert len(due_flashcards) == 0, "There should be no flashcards after deletion"

# Helper function to retrieve a flashcard by its ID
def get_flashcard_by_id(card_id):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT id, front, back, created_at FROM flashcards WHERE id = ?', (card_id,))
    flashcard = cursor.fetchone()
    conn.close()
    # Returning as a dictionary for easier access in assertions
    return {
        'id': flashcard[0],
        'front': flashcard[1],
        'back': flashcard[2],
        'created_at': flashcard[3]
    } if flashcard else None

# Helper function to retrieve review information by flashcard ID
def get_review_info_by_card_id(card_id):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT card_id, next_review, interval FROM review_schedule WHERE card_id = ?', (card_id,))
    review_info = cursor.fetchone()
    conn.close()
    # Returning as a dictionary for easier access in assertions
    return {
        'card_id': review_info[0],
        'next_review': review_info[1],
        'interval': review_info[2]
    } if review_info else None