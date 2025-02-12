import json
import sqlite3
from pathlib import Path

def load_json_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def seed_words():
    # Connect to database
    conn = sqlite3.connect('../words.db')
    cursor = conn.cursor()
    
    # Get the directory containing this script
    seed_dir = Path(__file__).parent
    
    # Load word data
    nouns = load_json_file(seed_dir / 'data_nouns.json')['nouns']
    adjectives = load_json_file(seed_dir / 'data_adjectives.json')['adjectives']
    verbs = load_json_file(seed_dir / 'data_verbs.json')['verbs']
    
    # Clear existing words
    cursor.execute('DELETE FROM words')
    
    # Insert words
    for word_list in [nouns, adjectives, verbs]:
        for word in word_list:
            cursor.execute('''
                INSERT INTO words (german, pronunciation, english, article, word_type, additional_info)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                word['german'],
                word.get('pronunciation'),
                word['english'],
                word.get('article'),  # Only nouns have articles
                word['word_type'],
                json.dumps(word['additional_info'])
            ))
    
    # Commit changes
    conn.commit()
    conn.close()
    print("Word data seeded successfully!")

if __name__ == '__main__':
    seed_words()