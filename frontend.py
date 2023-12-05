import os
from datetime import datetime
from typing import Tuple, List
from datetime import datetime, timedelta

from db import client
import logging
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
import webvtt


import spacy
NEW_CARDS_DAILY_LIMIT = 20

# Load the Spanish tokenizer
nlp = spacy.load('es_core_news_sm')
vtt_file_path = Path('test-corpus/whiplash/Whiplash.es.vtt')


import json
import os

current_simulated_date = datetime.now()

def advance_simulated_day(days=1):
    global current_simulated_date
    current_simulated_date += timedelta(days=days)


def extract_caption_text(file_path: Path) -> list[str]:
    """Extract all caption lines from a vtt file."""
    return [line.text for line in webvtt.read(str(file_path))]


def clean_caption(caption: str) -> str:
    """Clean up peculiarities in vtt files."""
    caption = caption.replace('\n', ' ').replace('-', '')
    caption = caption.lower().strip()
    return caption


def load_corpus_stats(json_folder_path):
    corpus_stats = {}
    for filename in os.listdir(json_folder_path):
        if filename.endswith('.json'):
            file_path = os.path.join(json_folder_path, filename)
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                corpus_stats.update(data)
    return corpus_stats

json_folder_path = 'test-corpus/whiplash'
corpus_stats = load_corpus_stats(json_folder_path)

#Using Corpus Stats in SRS Logic: Ensure that wherever you initialize token difficulties (like in the add_sentence function), you pass the corpus_stats dictionary to it.

def tokenize_sentence(sentence):
    # Process the sentence using the spaCy model
    doc = nlp(sentence)
    # Extract the lemmas of the tokens from the doc
    lemmas = [token.lemma_ for token in doc]
    return lemmas

def initialize_token_difficulties(sentence, corpus_stats):
    tokens = tokenize_sentence(sentence)
    token_data = {}
    for token in tokens:
        stats = corpus_stats.get(token, {})
        token_data[token] = {
            "difficulty": stats.get("word_importance", 100),
            "encounters": 0,
            "fails": 0,
            "tfidf": stats.get("tfidf", 0.5),
            "word_importance": stats.get("word_importance", 0.5)
        }
    return token_data

def generate_tokens_with_metadata(sentence, corpus_stats):
    tokens = tokenize_sentence(sentence)
    tokens_with_metadata = initialize_token_difficulties(sentence, corpus_stats)
    return tokens_with_metadata


def calculate_sentence_score(tokens):
    tfidf_scores = [data['tfidf'] for token, data in tokens.items()]
    average_tfidf = sum(tfidf_scores) / len(tfidf_scores) if tfidf_scores else 0

    d_s_scores = [data['word_importance'] ** 4 for token, data in tokens.items()]
    d_s_score = (sum(d_s_scores) ** (1/4)) if d_s_scores else 0

    # You can adjust these weights
    alpha, beta = 0.5, 0.5
    return alpha * average_tfidf + beta * d_s_score


def add_user(client, email, password_hash):
    # Correctly formatted query to check if the user exists
    existing_user = client.table("users").select("email").eq("email", email).execute()

    if existing_user.data:
        return {"error": "User with this email already exists."}

    data = {
        "email": email,
        "password_hash": password_hash,
        "created_at": current_simulated_date.strftime('%Y-%m-%d %H:%M:%S')
    }

    result = client.table("users").insert(data).execute()
    return result

def get_due_flashcards(client, email):
    # Retrieve user_id based on email
    user = client.table("users").select("id").eq("email", email).execute()
    if not user.data:
        return {"error": "User not found."}

    user_id = user.data[0]['id']
    today = current_simulated_date.strftime('%Y-%m-%d')

    query = (
        client.table("review_schedule")
        .select("*, flashcards(*)")
        .eq("user_id", user_id)
        .lte("next_review", today)
        .execute()
    )

    if 'error' in query:
        return query

    review_cards = [card for card in query.data if card['last_reviewed'] != None]


    # Assuming `query.data` contains the fetched data with the flashcards included
    new_cards_raw = [card for card in query.data if card['last_reviewed'] == None]

    # Since the flashcards are nested within the query results, we'll need to sort them by 'sentence_score' in a slightly different way.
    # We'll extract the sentence_score and sort the flashcards accordingly.
    sorted_new_cards = sorted(new_cards_raw, key=lambda card: card['flashcards']['sentence_score'] if 'flashcards' in card and 'sentence_score' in card['flashcards'] else 0, reverse=True)

    # Apply the daily new card limit after sorting
    sorted_new_cards = sorted_new_cards[:NEW_CARDS_DAILY_LIMIT]

    # Here, we assume `review_cards` is already defined elsewhere, similar to `new_cards`
    # Return the sorted new cards along with the review cards
    return sorted_new_cards + review_cards

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

def add_sentence(client, user_id, front, back, corpus_stats):
    try:
        # Tokenize and initialize difficulties only for the back of the card
        back_tokens_difficulty = initialize_token_difficulties(back, corpus_stats)
        
        flashcard_data = {
            "user_id": user_id,
            "front": front,
            "back": back,
            "tokens": back_tokens_difficulty,  # Store just the back tokens
            "created_at": current_simulated_date.strftime('%Y-%m-%d %H:%M:%S'),
            "status": "new"
        }


        sentence_score = calculate_sentence_score(back_tokens_difficulty)
        # Add sentence score to flashcard_data
        flashcard_data['sentence_score'] = sentence_score

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
            "next_review": current_simulated_date.strftime('%Y-%m-%d'),
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
def answer_flashcard(client, review_schedule_id, known_tokens, unknown_tokens):
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

        # Determine the need for immediate re-review
        total_tokens = len(updated_tokens_back)
        unknown_count = len(unknown_tokens)
        unknown_ratio = unknown_count / total_tokens if total_tokens else 0

        immediate_review_threshold = 0.5  # Threshold for determining immediate re-review
        needs_immediate_review = unknown_ratio >= immediate_review_threshold

        # Calculate new interval
        new_interval = calculate_new_interval(review_data['interval'], updated_tokens_back, needs_immediate_review)

        # Set the next review date
        next_review_date = current_simulated_date if needs_immediate_review else (current_simulated_date + timedelta(days=new_interval))

        # Update the flashcard with new token difficulties
        update_flashcard = client.table("flashcards").update({"tokens": updated_tokens_back}).eq("id", card_id).execute()

        # Change the status from 'new' to 'learning' if applicable
        if flashcard_data['status'] == 'new':
            flashcard_data['status'] = 'learning'
            client.table("flashcards").update({"status": flashcard_data['status']}).eq("id", card_id).execute()
    
        # Update review count and next review date in the review schedule
        update_data = {
            "next_review": next_review_date.strftime('%Y-%m-%d'),
            "interval": new_interval,
            "review_count": review_data['review_count'] + 1,
            "success_count": review_data['success_count'] + (0 if needs_immediate_review else 1)
        }
    
        # Update review schedule entry with new data
        result = client.table("review_schedule").update(update_data).eq("id", review_schedule_id).execute()
        return result
    except Exception as e:
        return {"error": str(e)}

    
def classify_tokens(tokens_with_metadata, difficulty_threshold=50, encounter_threshold=3):
    known_tokens = []
    unknown_tokens = []

    for token, data in tokens_with_metadata.items():
        if data['difficulty'] <= difficulty_threshold and data['encounters'] >= encounter_threshold:
            known_tokens.append(token)
        else:
            unknown_tokens.append(token)

    return known_tokens, unknown_tokens



def calculate_card_difficulty(tokens):
    return sum([data['difficulty'] for token, data in tokens.items()]) / len(tokens) if tokens else 0


def select_next_card(cards):
    # Assuming cards is a list of flashcards with 'sentence_score' and 'token_familiarity'
    # Sort cards by a combination of their score and token familiarity
    sorted_cards = sorted(cards, key=lambda x: (x['sentence_score'], x['token_familiarity']), reverse=True)
    return sorted_cards[0] if sorted_cards else None

def calculate_new_interval(current_interval, tokens, needs_immediate_review):
    base_interval = current_interval * (0.5 if needs_immediate_review else 2)
    token_familiarity = sum([t['encounters'] for t in tokens.values()]) / len(tokens)
    sentence_score = calculate_sentence_score(tokens)

    # Adjust weights as needed
    gamma, delta = 0.3, 0.2
    adjusted_interval = base_interval * (1 + gamma * token_familiarity + delta * sentence_score)
    return max(1, int(adjusted_interval))

def manage_intra_day_reviews(user_sessions):
    # Logic to distribute reviews based on user performance and card difficulty
    # Adjust the review schedule dynamically within the day
    pass

def adjust_interval_by_difficulty(interval, card_difficulty):
    # For easy cards, extend the interval, and for difficult cards, shorten it.
    difficulty_adjustment = 1.0 - min(0.3, card_difficulty / 300)  # Example adjustment factor
    return max(1, int(interval * difficulty_adjustment))
    
def get_next_card_due_for_user(client, user_id):
    try:
        today = current_simulated_date.strftime('%Y-%m-%d')
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

# -- Run Tests --

if __name__ == "__main__":

    clear_result = clear_all_tables(client)

    captions = extract_caption_text(vtt_file_path)
    cleaned_captions = [clean_caption(caption) for caption in captions]

    dummy_email = "dummy_user@example.com"
    dummy_password_hash = "hashed_dummy_password"  # In a real scenario, this should be a properly hashed password
    add_user(client, dummy_email, dummy_password_hash)

    dummy_user_id = get_user_id_by_email(client, dummy_email)

    for i in range(min(50, len(cleaned_captions))):  # This ensures it doesn't go beyond the list length
        caption = cleaned_captions[i]
        front = caption  # or some transformation of caption
        back = caption   # or some transformation of caption
        add_sentence(client, dummy_user_id, front, back, corpus_stats)

    import random

    for day in range(1, 31):  # Simulate for 30 days, for example
        due_cards = get_due_flashcards(client, dummy_email)
        # Example usage within your main loop
        # Assuming 'front' contains the text for the front of the card and tokens are stored for each card
        for card in due_cards:
            front = card['flashcards']['front']
            tokens = card['flashcards']['tokens']# You would need to align this with your flashcard data structure
            known_tokens, unknown_tokens = classify_tokens(tokens)

            # Use these lists in your answer_flashcard function call
            answer_flashcard(client, card['id'], known_tokens, unknown_tokens)

# #####

# -- Test Functions --

# from datetime import datetime

# def test_add_user(client):
#     print("Testing: Add User")
#     new_user_email = "newuser@example.com"
#     new_user_password_hash = "hashed_password"
#     result = add_user(client, new_user_email, new_user_password_hash)
#     if 'error' in result:
#         print(f"Error: {result['error']}")
#     else:
#         print("Successfully added new user:", result)
#     return result

# def test_get_user_id(client, email):
#     print(f"Testing: Get User ID for {email}")
#     user_id = get_user_id_by_email(client, email)
#     if user_id:
#         print(f"User ID for {email}: {user_id}")
#     else:
#         print(f"User not found for {email}")
#     return user_id

# def test_add_and_get_flashcards(client, user_id, email):
#     print("Testing: Add and Retrieve Flashcards")
#     front = "Example sentence"
#     back = "traduccion"
#     add_result = add_sentence(client, user_id, front, back, corpus_stats)
#     print("Add Flashcard Result:", add_result)

#     due_flashcards = get_due_flashcards(client, email)
#     print("Due Flashcards:", due_flashcards)
#     return due_flashcards

# def test_answer_flashcard(client, user_id, card_id, known_tokens, unknown_tokens):
#     print("Testing: Answer Flashcard")
#     correct = True  # Assume correct for the test scenario
#     result = answer_flashcard(client, card_id, correct, known_tokens, unknown_tokens)
#     print("Answer Flashcard Result:", result)

# def run_all_tests(client):
#     # Clear tables before running tests
#     print("Clearing all tables")
#     clear_all_tables(client)

#     # Test adding a user
#     user_result = test_add_user(client)
#     if 'error' in user_result:
#         print("Error adding user, skipping further tests.")
#         return

#     email = "newuser@example.com"  # Assuming this is the email used in test_add_user
#     user_id = test_get_user_id(client, email)

#     # Test adding and retrieving flashcards
#     if not user_id:
#         print("User ID not found, skipping flashcard tests.")
#         return

#     due_flashcards = test_add_and_get_flashcards(client, user_id, email)
#     if 'error' in due_flashcards or not due_flashcards[0]:
#         print("No due flashcards found or error, skipping answer flashcard test.")
#         return

#     # Assume the first due flashcard is the one to be answered
#     card_id = due_flashcards[0]['id']

#     # Example tokens known or unknown to the user
#     known_tokens = ["traduccion"]
#     unknown_tokens = []

#     # Test answering a flashcard
#     test_answer_flashcard(client, user_id, card_id, known_tokens, unknown_tokens)

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
