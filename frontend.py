import os
from datetime import datetime
from typing import Tuple, List
from datetime import datetime, timedelta

from db import client
from stuff.heuristic import *
import logging

from datetime import datetime

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

clear_result = clear_all_tables(client)
print(clear_result)


# Example usage
new_user_email = "example@example.com"
new_user_password_hash = "hashed_password_here"
user_add_result = add_user(client, new_user_email, new_user_password_hash)

# Fetch the user ID for the newly created user
user_id = get_user_id_by_email(client, new_user_email)

if user_id is not None:
    print(f"User ID for {new_user_email} is {user_id}")
    # Now you can use this user_id for further operations like adding sentences
    # ...
else:
    print("User not found or error occurred.")

def add_sentence(client, user_id, front, back):
    try:
        # First, insert the new flashcard
        flashcard_data = {
            "user_id": user_id,
            "front": front,
            "back": back,
            "tokens": {},  # Adjust this based on your schema
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

    
# Example usage
front = "Example sentence"
back = "Meaning or translation of the sentence"

add_sentence_result = add_sentence(client, user_id, front, back)
print(add_sentence_result)



def answer_flashcard(client, user_id, correct):
    try:
        # Retrieve the next card due for the user
        card_id = get_next_card_due_for_user(client, user_id)
        if card_id is None:
            return {"error": "No cards due for review"}

        # Retrieve the current review schedule for the card
        current_review = client.table("review_schedule").select("*").eq("user_id", user_id).eq("card_id", card_id).execute()

        if not current_review.data:
            return {"error": "Review schedule not found."}

        review_data = current_review.data[0]
        new_interval = calculate_new_interval(review_data['interval'], correct)
        next_review_date = datetime.now() + timedelta(days=new_interval)

        # Update review count, success count, and next review date
        update_data = {
            "next_review": next_review_date.strftime('%Y-%m-%d'),
            "interval": new_interval,
            "review_count": review_data['review_count'] + 1,
            "success_count": review_data['success_count'] + (1 if correct else 0)
        }

        result = client.table("review_schedule").update(update_data).eq("id", review_data['id']).execute()
        return result
    except Exception as e:
        return {"error": str(e)}


def calculate_new_interval(current_interval, correct):
    # Implement your logic for the next interval
    # For example, increase the interval if the answer was correct, and decrease if it was incorrect
    if correct:
        return current_interval * 2  # Example: double the interval if correct
    else:
        return max(1, current_interval // 2)  # Example: halve the interval if incorrect, but not less than 1 day
    
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
# Fetch user ID
user_email = "example@example.com"
user_id = get_user_id_by_email(client, user_email)

# Fetch the next card due for review
next_card_due_id = get_next_card_due_for_user(client, user_id)

if next_card_due_id is not None:
    print(f"Next card due for user {user_id} is card ID {next_card_due_id}")
    # Here you can proceed to show this flashcard to the user for review
else:
    print("No cards due for review or error occurred.")