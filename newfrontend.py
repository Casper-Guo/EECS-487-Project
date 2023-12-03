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

def get_next_flashcard(user_id: int) -> Tuple[int, str, str]:
    """
    Retrieves the next flashcard for a given user based on their user ID and the due date.

    Args:
    - user_id: An integer representing the unique ID of the user.

    Returns:
    A tuple containing the flashcard ID, front text, and back text. Returns an empty tuple if there are no more cards due for the day.
    """
    query = (client.table('review_schedule')
                   .select('flashcards.id, flashcards.front, flashcards.back')
                   .join('flashcards', 'flashcards.id', 'review_schedule.card_id')
                   .filter('review_schedule.user_id', 'eq', user_id)
                   .filter('review_schedule.next_review', 'lte', datetime.datetime.utcnow())
                   .order('review_schedule.next_review')
                   .limit(1)
                   .execute())

    if len(query.data) == 0:
        return ()
    else:
        card = query.data[0]
        return card['id'], card['front'], card['back']

def save_review(user_id: int, flashcard_id: int, success: bool):
    """
    Saves the review of a flashcard and updates the review schedule.

    Args:
    - user_id: User ID.
    - flashcard_id: Flashcard ID.
    - success: Boolean indicating if the review was successful.

    Returns:
    None
    """
    # Fetch the current review data
    review_data = client.table('review_schedule').select('*').eq('card_id', flashcard_id).eq('user_id', user_id).execute().data[0]

    # Update the review count and success count
    review_data['review_count'] += 1
    if success:
        review_data['success_count'] += 1

    # Calculate the next review date
    next_review_date, new_interval = calculate_next_review_date(review_data['last_reviewed'], review_data['interval'], success)
    review_data['next_review'] = next_review_date
    review_data['last_reviewed'] = datetime.datetime.utcnow()
    review_data['interval'] = new_interval

    # Update the review schedule
    client.table('review_schedule').update(review_data).eq('id', review_data['id']).execute()

def calculate_next_review_date(last_reviewed: datetime.datetime, current_interval: int, success: bool) -> Tuple[datetime.datetime, int]:
    """
    Calculates the next review date for a flashcard.

    Args:
    - last_reviewed: The datetime when the card was last reviewed.
    - current_interval: The current interval in days.
    - success: Boolean indicating if the review was successful.

    Returns:
    A tuple of the next review datetime and the new interval.
    """
    if success:
        new_interval = current_interval * 2  # Example of interval increase
    else:
        new_interval = max(1, current_interval // 2)  # Example of interval decrease

    next_review_date = datetime.datetime.utcnow() + datetime.timedelta(days=new_interval)
    return next_review_date, new_interval

def delete_all_flashcards(user_id: int):
    """
    Deletes all flashcards for a given user.

    Args:
    - user_id: User ID.

    Returns:
    None
    """
    client.table('flashcards').delete().eq('user_id', user_id).execute()

def flashcard_statistics(user_id: int) -> str:
    """
    Prints statistics for a user's flashcards.

    Args:
    - user_id: User ID.

    Returns:
    String representation of the statistics.
    """
    total_flashcards = client.table('flashcards').select('*').eq('user_id', user_id).execute().count
    due_today = client.table('review_schedule').select('*').eq('user_id', user_id).filter('next_review', 'lte', datetime.datetime.utcnow()).execute().count

    return f"Total flashcards: {total_flashcards}, Due today: {due_today}"

# Additional functions like 'add_user', etc., would remain largely the same, 
# perhaps with minor tweaks to align with the new database structure.
