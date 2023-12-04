import os
from datetime import datetime
from typing import Tuple, List
from datetime import datetime, timedelta

from db import client
import logging
import re
from collections import defaultdict
from datetime import datetime

def tokenize_sentence(sentence):
    return re.findall(r'\b\w+\b', sentence.lower())

def initialize_token_difficulties(sentence):
    tokens = tokenize_sentence(sentence)
    initial_difficulty = 100  # A default starter score for token difficulty
    return {token: {"difficulty": initial_difficulty, "encounters": 0, "fails": 0} for token in tokens}

def add_user(client, email, password_hash):
    # Correctly formatted query to check if the user exists
    existing_user = client.table("users").select("email").eq("email", email).execute()

    if existing_user.data:
        return {"error": "User with this email already exists."}

    data = {
        "email": email,
        "password_hash": password_hash,
        "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    result = client.table("users").insert(data).execute()
    return result

def get_due_flashcards(client, email):
    # Retrieve user_id based on email
    user = client.table("users").select("id").eq("email", email).execute()
    if not user.data:
        return {"error": "User not found."}

    user_id = user.data[0]['id']
    today = datetime.now().strftime('%Y-%m-%d')

    query = (
        client.table("review_schedule")
        .select("*, flashcards(*)")
        .eq("user_id", user_id)
        .lte("next_review", today)
        .execute()
    )

    if 'error' in query:
        return query

    return query.data

def clear_all_tables(client):
    try:
        client.table("review_schedule").delete().gte("id", 0).execute()
        client.table("flashcards").delete().gte("id", 0).execute()
        client.table("users").delete().gte("id", 0).execute()
        return {"success": "All tables cleared."}
    except Exception as e:
        return {"error": str(e)}


def get_user_id_by_email(client, email):
    try:
        user_record = client.table("users").select("id").eq("email", email).execute()
        if user_record.data:
            return user_record.data[0]['id']
        else:
            return None
    except Exception as e:
        print("Error fetching user ID:", str(e))
        return None

def add_sentence(client, user_id, front, back):
    try:
        # Tokenize and initialize difficulties only for the back of the card
        back_tokens_difficulty = initialize_token_difficulties(back)
        
        flashcard_data = {
            "user_id": user_id,
            "front": front,
            "back": back,
            "tokens": back_tokens_difficulty,  # Store just the back tokens
            "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        flashcard_result = client.table("flashcards").insert(flashcard_data).execute()


        if hasattr(flashcard_result, 'data'):
            flashcard_data = flashcard_result.data
            if flashcard_data and isinstance(flashcard_data, list):
                new_card_id = flashcard_data[0]['id']
                # ... continue with your logic ...
            else:
                return {"error": "No data returned or invalid format"}
        else:
            return {"error": "Unexpected response structure from API"}
        
        # Then, create an entry in the review_schedule table
        review_data = {
            "user_id": user_id,
            "card_id": new_card_id,
            "next_review": datetime.now().strftime('%Y-%m-%d'),
            "interval": 1,  # Starting interval, adjust as needed
            "last_reviewed": None,
            "review_count": 0,
            "success_count": 0
        }
        review_result = client.table("review_schedule").insert(review_data).execute()

        return review_result
    except Exception as e:
        return {"error": str(e)}
    
def update_token_difficulties(tokens, known_tokens, unknown_tokens):
    known_difficulty_adjustment = -5
    unknown_difficulty_adjustment = 10

    for token in known_tokens:
        if token in tokens:
            tokens[token]["difficulty"] += known_difficulty_adjustment
            tokens[token]["difficulty"] = max(0, tokens[token]["difficulty"])  # Avoid negative difficulty
            tokens[token]["encounters"] += 1

    for token in unknown_tokens:
        if token in tokens:
            tokens[token]["difficulty"] += unknown_difficulty_adjustment
            tokens[token]["difficulty"] = max(0, tokens[token]["difficulty"])
            tokens[token]["encounters"] += 1
            tokens[token]["fails"] += 1

    return tokens

def answer_flashcard(client, review_schedule_id, correct, known_tokens, unknown_tokens):
    try:
        # Fetch review schedule by the review schedule id
        current_review = client.table("review_schedule").select("*").eq("id", review_schedule_id).execute()
        if not current_review.data:
            return {"error": "Review schedule not found."}
    
        review_data = current_review.data[0]
        card_id = review_data['card_id']  # Use the actual card_id from the review_schedule table
    
        # Retrieve the flashcard by its card_id to update tokens
        current_flashcard = client.table("flashcards").select("*").eq("id", card_id).execute()
        if not current_flashcard.data:
            return {"error": "Flashcard not found."}
    
        flashcard_data = current_flashcard.data[0]
        flashcard_tokens_back = flashcard_data["tokens"]  # Assume tokens are only for the back
    
        # Update the back tokens with the known and unknown feedback from the user
        updated_tokens_back = update_token_difficulties(flashcard_tokens_back, known_tokens, unknown_tokens)
    
        # Save updated back tokens to the database
        update_flashcard = client.table("flashcards").update({"tokens": updated_tokens_back}).eq("id", card_id).execute()
    
        # Calculate the new interval based on updated back token difficulties
        new_interval = calculate_new_interval(review_data['interval'], correct, updated_tokens_back)
        next_review_date = datetime.now() + timedelta(days=new_interval)
    
        # Update review count, success count, and next review date
        update_data = {
            "next_review": next_review_date.strftime('%Y-%m-%d'),
            "interval": new_interval,
            "review_count": review_data['review_count'] + 1,
            "success_count": review_data['success_count'] + (1 if correct else 0)
        }
    
        # Update review schedule entry with new interval and counts
        result = client.table("review_schedule").update(update_data).eq("id", review_schedule_id).execute()
        return result
    except Exception as e:
        return {"error": str(e)}


def calculate_card_difficulty(tokens):
    return sum([data['difficulty'] for token, data in tokens.items()]) / len(tokens) if tokens else 0

def calculate_new_interval(current_interval, correct, tokens):
    base_interval = current_interval * 2 if correct else max(1, current_interval // 2)
    card_difficulty = calculate_card_difficulty(tokens)
    return adjust_interval_by_difficulty(base_interval, card_difficulty)

def adjust_interval_by_difficulty(interval, card_difficulty):
    # For easy cards, extend the interval, and for difficult cards, shorten it.
    difficulty_adjustment = 1.0 - min(0.3, card_difficulty / 300)  # Example adjustment factor
    return max(1, int(interval * difficulty_adjustment))
    
def get_next_card_due_for_user(client, user_id):
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        next_card_query = (
            client.table("review_schedule")
            .select("card_id")
            .eq("user_id", user_id)
            .lte("next_review", today)
            .order("next_review")  # Default order is ascending
            .limit(1)
            .execute()
        )

        if next_card_query.data:
            return next_card_query.data[0]['card_id']
        else:
            return None
    except Exception as e:
        print("Error fetching next card due:", str(e))
        return None

# -- Test Functions --

from datetime import datetime

def test_add_user(client):
    print("Testing: Add User")
    new_user_email = "newuser@example.com"
    new_user_password_hash = "hashed_password"
    result = add_user(client, new_user_email, new_user_password_hash)
    if 'error' in result:
        print(f"Error: {result['error']}")
    else:
        print("Successfully added new user:", result)
    return result

def test_get_user_id(client, email):
    print(f"Testing: Get User ID for {email}")
    user_id = get_user_id_by_email(client, email)
    if user_id:
        print(f"User ID for {email}: {user_id}")
    else:
        print(f"User not found for {email}")
    return user_id

def test_add_and_get_flashcards(client, user_id, email):
    print("Testing: Add and Retrieve Flashcards")
    front = "Example sentence"
    back = "Translation"
    add_result = add_sentence(client, user_id, front, back)
    print("Add Flashcard Result:", add_result)

    due_flashcards = get_due_flashcards(client, email)
    print("Due Flashcards:", due_flashcards)
    return due_flashcards

def test_answer_flashcard(client, user_id, card_id, known_tokens, unknown_tokens):
    print("Testing: Answer Flashcard")
    correct = True  # Assume correct for the test scenario
    result = answer_flashcard(client, card_id, correct, known_tokens, unknown_tokens)
    print("Answer Flashcard Result:", result)

def run_all_tests(client):
    # Clear tables before running tests
    print("Clearing all tables")
    clear_all_tables(client)

    # Test adding a user
    user_result = test_add_user(client)
    if 'error' in user_result:
        print("Error adding user, skipping further tests.")
        return

    email = "newuser@example.com"  # Assuming this is the email used in test_add_user
    user_id = test_get_user_id(client, email)

    # Test adding and retrieving flashcards
    if not user_id:
        print("User ID not found, skipping flashcard tests.")
        return

    due_flashcards = test_add_and_get_flashcards(client, user_id, email)
    if 'error' in due_flashcards or not due_flashcards[0]:
        print("No due flashcards found or error, skipping answer flashcard test.")
        return

    # Assume the first due flashcard is the one to be answered
    card_id = due_flashcards[0]['id']

    # Example tokens known or unknown to the user
    known_tokens = ["translation"]
    unknown_tokens = []

    # Test answering a flashcard
    test_answer_flashcard(client, user_id, card_id, known_tokens, unknown_tokens)

# -- Run Tests --

if __name__ == "__main__":
    run_all_tests(client)


# #####

# clear_result = clear_all_tables(client)
# print(clear_result)

# # Example usage
# new_user_email = "example@example.com"
# new_user_password_hash = "hashed_password_here"
# user_add_result = add_user(client, new_user_email, new_user_password_hash)

# # Fetch the user ID for the newly created user
# user_id = get_user_id_by_email(client, new_user_email)

# if user_id is not None:
#     print(f"User ID for {new_user_email} is {user_id}")
#     # Now you can use this user_id for further operations like adding sentences
#     # ...
# else:
#     print("User not found or error occurred.")

    
# # Example usage
# front = "Example sentence"
# back = "Meaning or translation of the sentence"

# add_sentence_result = add_sentence(client, user_id, front, back)
# print(add_sentence_result)

# # Fetch user ID
# user_email = "example@example.com"
# user_id = get_user_id_by_email(client, user_email)

# # Fetch the next card due for review
# next_card_due_id = get_next_card_due_for_user(client, user_id)

# if next_card_due_id is not None:
#     print(f"Next card due for user {user_id} is card ID {next_card_due_id}")
#     # Here you can proceed to show this flashcard to the user for review
# else:
#     print("No cards due for review or error occurred.")
