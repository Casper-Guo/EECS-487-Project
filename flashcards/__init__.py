import os

# Define 'db_path' for the whole package
current_dir = os.path.dirname(os.path.realpath(__file__))
db_path = os.path.join(current_dir, 'flashcards.db')
