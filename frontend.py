import os
from datetime import datetime
from typing import Tuple, List
from datetime import datetime, timedelta

import pytz
import configparser
import openai

from db import client
from stuff.heuristic import *
import logging

def get_next_card(user_id: int) -> Tuple[int, str, str, str]:
    """
    Retrieves the next flashcard for a given user based on their user ID.

    Args:
    - user_id: An integer representing the unique ID of the user.

    Returns:
    A tuple containing the ID, sentence text, translation, and image URL of the next flashcard. Returns an empty tuple if there are no more cards for the day.
    """

    # Select the card with the earliest 'next_review_date' that has not been seen today
    query = (client.table('sentences').select('*').filter('user_id', 'eq', user_id).filter('next_review_date', 'lte', datetime.utcnow()).filter('seen_today', 'eq', False).order('next_review_date').limit(1).execute())

    if len(query.data) == 0:
        return ()
    else:
        card = query.data[0]
        return card['sentence_id'], card['text'], card['translation'], card['image_url']


def save_answers(sentence_id: int, answers: List[Tuple[int, bool]]):
    """
    Saves answers for a sentence in the database.
    It updates the 'seen_today' column and the 'next_review_date' in the 'sentences' table and inserts new rows in the 'answers' table for each token_id and answer in the given pairs.

    :param sentence_id: ID of the sentence for which the answers are saved. (int)
    :param answers: List of pairs containing token_id and answer for each token in the sentence. (list of tuples)

    :return: None
    """
    next_review_date = calculate_next_review_date(sentence_id, answers, client)
    next_review_date_utc = next_review_date.replace(tzinfo=pytz.UTC)
    client.table('sentences').update({'seen_today': True, 'next_review_date': next_review_date_utc.isoformat()}).eq('sentence_id', sentence_id).execute()

    # Insert new rows in the 'answers' table for each token_id and answer in the given pairs
    for token_id, answer in answers:
        answer_data = {'sentence_id': sentence_id, 'token_id': token_id, 'answer': answer}
        client.table('answers').insert([answer_data]).execute()

        # Update the familiarity values for all instances of the same token lemma
        token = client.table('tokens').select('*').eq('token_id', token_id).execute().data[0]
        lemma = token['lemma']
        new_familiarity = update_familiarity(token['familiarity'], answer)
        client.table('tokens').update({'familiarity': new_familiarity}).eq('lemma', lemma).execute()

def update_familiarity(current_familiarity: float, answer: bool) -> float:
    """
    Update the familiarity value based on the user's answer.

    :param current_familiarity: The current familiarity value. (float)
    :param answer: The user's answer (True if correct, False if incorrect). (bool)

    :return: The updated familiarity value. (float)
    """

    # Update the familiarity value based on the user's answer
    if answer:
        new_familiarity = min(current_familiarity + 0.1, 1.0)
    else:
        new_familiarity = max(current_familiarity - 0.1, 0.0)

    return new_familiarity

class EmptyTokensListError(Exception):
    pass

def calculate_next_review_date(sentence_id: int, answers: List[Tuple[int, bool]], client, interval_factor: float = 1.0) -> datetime:

    """
    Calculate the next review date for a sentence based on the user's answers.

    :param sentence_id: ID of the sentence for which the answers are provided. (int)
    :param answers: List of pairs containing token_id and answer for each token in the sentence. (list of tuples)
    :param client: The database client used to retrieve and update data.
    :param interval_factor: The factor to adjust the review interval. (float, optional)

    :return: The calculated next review date. (datetime)
    """
    # Retrieve the tokens data
    tokens = client.table('tokens').select('*').eq('sentence_id', sentence_id).execute().data

    # If the tokens list is empty, log a debug message and raise a custom exception
    #The `tokens` list could be empty if there's an issue with inserting tokens into the database, or if there are no valid tokens
    # (e.g., only punctuation or proper nouns) in a sentence when the `include_proper_nouns` flag is set to `False`.
    if not tokens:
        print(f"Debug: No tokens found for sentence ID {sentence_id}. Please check the database and sentence generation.")
        raise EmptyTokensListError(f"No tokens found for sentence ID {sentence_id}")

    # Calculate the average familiarity of the tokens in the sentence
    avg_familiarity = sum(token['familiarity'] for token in tokens) / len(tokens)

    # Update the familiarity values for each token based on the user's answers
    for token_id, answer in answers:
        token = [t for t in tokens if t['token_id'] == token_id][0]
        token['familiarity'] = update_familiarity(token['familiarity'], answer)
        client.table('tokens').update(token).eq('token_id', token_id).execute()

    # SRS Algorithm (SM-2-like): Calculate the next review date based on the user's selected tokens
    selected_tokens_familiarity = [token['familiarity'] for token_id, answer in answers if answer for token in (t for t in tokens if t['token_id'] == token_id)]

    if selected_tokens_familiarity:
        avg_selected_familiarity = sum(selected_tokens_familiarity) / len(selected_tokens_familiarity)
        # Weighted average of the average familiarity and the average selected familiarity
        weighted_familiarity = 0.6 * avg_familiarity + 0.4 * avg_selected_familiarity
        review_interval = timedelta(days=round((1 - weighted_familiarity) * 10))
    else:
        review_interval = timedelta(days=1)  # Default review interval for new sentences

    # Calculate the adjusted review interval using the interval factor and familiarity
    adjusted_review_interval = timedelta(days=int(review_interval.total_seconds() / 86400 * interval_factor))

    # Return the calculated next review date
    return datetime.utcnow() + adjusted_review_interval

def add_user(name, db_client):
    # Check if user exists
 # Gets or creates a logger

    result = db_client.table('users').select('*').eq('name', name).execute()
    if result.data:
        user_id = result.data[0]['user_id']
        return user_id
    else:
        # User doesn't exist, create a new one
        try:
            result = db_client.from_('users').insert({
                'name': name,
                'target_language': 'en'  # Set a default target language
            }).execute()
            user_id = result.data[0]['user_id']
            return user_id
        except:
            print("Couldn't add a user for some reason")
            return -1