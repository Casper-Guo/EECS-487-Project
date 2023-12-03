import os
import random
from datetime import datetime, date
from typing import Tuple

import pandas as pd
import numpy as np
import pytz
import spacy
from dateutil.parser import parse
from datetime import datetime, timezone
import openai

from configsfile import *
from db import client
from frontend import *
import string
# from server import app

import logging

"""
This module provides functions to interact with a database and generate sentences.
It contains helper functions to manipulate the database and driver functions for main functionalities.
"""

##############
# Helper Functions
##############

# def is_good_sentence(sentence: str) -> bool:
#     """
#     Checks if the generated sentence meets the quality criteria.

#     Args:
#     - sentence: A string representing the generated sentence.

#     Returns:
#     A boolean indicating if the sentence meets the quality criteria or not.
#     """

#     # Check if the sentence is not empty or contains only whitespace characters
#     if sentence.strip() == '':
#         return False

#     # Check if the sentence is not entirely in uppercase
#     if sentence.isupper():
#         return False

#     # Check if the sentence does not contain only punctuation symbols
#     if all(char in string.punctuation for char in sentence):
#         return False

#     return True

#this one is for testing only
def clear_all_tables(clear_user=True):
    # connect to the Supabase database
    # define the table names and their corresponding primary key column names
    table_primary_keys = {
        'answers': 'answer_id',
        'sentences': 'sentence_id',
        'tokens': 'token_id',
        'users': 'user_id',
        'focus_words': 'word_id'
    }

    # loop through each table and clear all the entries
    for table_name, primary_key in table_primary_keys.items():
        # skip the users table if clear_user is False
        if not clear_user and table_name == 'users':
            continue

        # delete referencing records in the tokens table before deleting records in other tables
        if table_name == 'sentences':
            client.table('tokens').delete().filter('sentence_id', 'neq', 0).execute()

        # delete records in the table
        client.table(table_name).delete().filter(primary_key, 'neq', 0).execute()

def get_sentence_id(user_id: int, sentence_text: str) -> int:
    sentence = client.table('sentences').select('sentence_id').eq('user_id', user_id).eq('text', sentence_text).execute().data
    if len(sentence) > 0:
        return sentence[0]['sentence_id']
    else:
        return -1

##############
# Driver Functions
##############

def add_sentence(user_id, include_proper_nouns=False):
    sentence_text = generate_sentence(user_id)
    logger = logging.getLogger(__name__)  

    # set log level
    logger.setLevel(logging.DEBUG)

    # define file handler and set formatter
    file_handler = logging.FileHandler('logfile.log')
    formatter    = logging.Formatter('%(asctime)s : %(levelname)s : %(name)s : %(message)s')
    file_handler.setFormatter(formatter)

    # add file handler to logger
    logger.addHandler(file_handler)
    logging.debug("we called this add sentence function")
    
    try:
        # Load spanish tokenizer, tagger, parser, NER and word vectors
        nlp = spacy.load("es_core_news_lg", disable=['parser', 'ner'])

        # Add the sentencizer component to the pipeline
        if not nlp.has_pipe("sentencizer"):
            nlp.add_pipe("sentencizer")

        # Tokenize the sentence
        doc = nlp(sentence_text)

        # Check if sentence already exists
        sentence_query = client.table('sentences').select('sentence_id').eq('user_id', user_id).eq('text', sentence_text).execute()
        if len(sentence_query.data) != 0:
            # Sentence already exists, return False
            return False

        target_language = 'English'

        query = client.table('sentences').select('*').eq('user_id', user_id).eq('text', sentence_text).execute()

        # If no such record exists, insert the new record
        if len(query.data) == 0:
            sentence_data = {
                'user_id': user_id,
                'text': sentence_text,
                # 'translation': translate_text(sentence_text, target_language)
                # 'image_url': generate_image(sentence_text) # Image generation removed
            }
            sentence_insert = client.table('sentences').insert([sentence_data]).execute()
            sentence_id = sentence_insert.data[0]['sentence_id']
        else:
            print("A record with the same user_id and sentence_text already exists.")
            return -1

        # Insert tokens into tokens table if they don't already exist
        for token in doc:
            # Exclude punctuation and optionally exclude proper nouns
            if not token.is_punct and (include_proper_nouns or not token.pos_ == 'PROPN'):
                token_data = {'text': token.text, 'lemma': token.lemma_, 'familiarity': 0, 'delta': 0, 'sentence_id': sentence_id}
                client.table('tokens').insert([token_data]).execute()
        # app.logger.debug("something went right adding card") # Temporarily commented out
        return 1
    except Exception as e:
        print("something went wrong for some reason")
        # app.logger.debug(e) # Temporarily commented out
        return -1


# def create_wordbank(user_id, max=50):
#     # Get today's date
#     today = datetime.utcnow().date()

#     # Retrieve the user's tokens and their familiarity values by joining the 'tokens' and 'sentences' tables
#     tokens = (
#         client.from_('tokens')
#         .select('*, sentences!tokens_sentence_id_fkey(*)')
#         .eq('sentences.user_id', user_id)
#         .execute()
#     )

#     # Filter out tokens that have already appeared in sentences generated today
#     today_tokens = [token for token in tokens.data if parse(token['sentences']['created_at']).date() == today]
#     today_token_texts = [token['text'] for token in today_tokens]
#     available_tokens = [token for token in tokens.data if token['text'] not in today_token_texts]

#     # Calculate token probabilities based on familiarity values
#     token_probabilities = [np.exp(token['familiarity']) for token in available_tokens]
#     total_probability = sum(token_probabilities)
#     token_probabilities = [p / total_probability for p in token_probabilities]

#     # Pick tokens from the available_tokens list using weighted probabilities
#     if len(token_probabilities) == 0:
#         return ['el']
#     wordbank = []
#     while len(wordbank) < max:
#         chosen_token = np.random.choice(available_tokens, p=token_probabilities)
#         if chosen_token['text'] not in wordbank:
#             wordbank.append(chosen_token['text'])

#         # Break the loop if the wordbank size reaches the size of the available_tokens list
#         if len(wordbank) == len(available_tokens):
#             break

#     return wordbank

def generate_sentence(user_id):

    # while True:
    #     # Generate a prompt using the create_prompt function
    #     prompt = create_prompt(create_wordbank(user_id))

    #     # Call the OpenAI API to generate a response to the prompt
    #     completion = openai.Completion.create(
    #         engine=config['openai']['generation_model'],
    #         prompt=prompt,
    #         max_tokens=50,
    #         stop="END",
    #         temperature=.7,
    #         top_p=1,
    #     )

    #     # Get the generated response
    #     generated_sentence = completion.choices[0].text.strip()

    #     # Check if the generated sentence meets the quality criteria
    #     if is_good_sentence(generated_sentence):
    #         return generated_sentence

    return "This is a dummy sentence loll"