import unittest

import sys
import os
# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Now you can import from newfrontend.py
from newfrontend import get_next_flashcard, save_review, delete_all_flashcards, flashcard_statistics

from unittest.mock import patch
import datetime

class TestLanguageLearningApp(unittest.TestCase):

    def setUp(self):
        # This method will run before each test
        # Setup your test environment here
        pass

    @patch('your_module.client')
    def test_get_next_flashcard(self, mock_client):
        # Setup mock response
        mock_client.table.return_value.select.return_value.filter.return_value.order.return_value.limit.return_value.execute.return_value.data = [
            {'id': 1, 'front': 'Hello', 'back': 'Hola'}
        ]

        # Call the function
        result = get_next_flashcard(1)

        # Check the result
        self.assertEqual(result, (1, 'Hello', 'Hola'))

    @patch('your_module.client')
    def test_save_review(self, mock_client):
        # Setup mock responses and expectations
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {'id': 1, 'review_count': 5, 'success_count': 3, 'next_review': datetime.datetime.utcnow(), 'last_reviewed': datetime.datetime.utcnow(), 'interval': 1}
        ]

        # Call the function
        save_review(1, 1, True)

        # Assertions to check if the update method was called correctly can be added here

    @patch('your_module.client')
    def test_delete_all_flashcards(self, mock_client):
        # Call the function
        delete_all_flashcards(1)

        # Assertions to check if the delete method was called correctly can be added here

    @patch('your_module.client')
    def test_flashcard_statistics(self, mock_client):
        # Setup mock responses
        mock_client.table.return_value.select.return_value.eq.return_value.execute.return_value.count = 10

        # Call the function
        stats = flashcard_statistics(1)

        # Check the result
        self.assertIn('Total flashcards: 10', stats)

    # You can add more test cases as needed

if __name__ == '__main__':
    unittest.main()
