from flask import jsonify, g
from flask_cors import cross_origin
import logging

logger = logging.getLogger(__name__)

def load(app):
    @app.route('/api/word-groups', methods=['GET'])
    @cross_origin()
    def get_word_groups():
        try:
            cursor = app.db.cursor()
            cursor.execute('''
                SELECT 
                    id,
                    name,
                    description,
                    (
                        SELECT COUNT(*)
                        FROM word_group_assignments
                        WHERE word_group_id = word_groups.id
                    ) as word_count
                FROM word_groups
                ORDER BY name ASC
            ''')
            
            groups = cursor.fetchall()
            return jsonify([{
                'id': group['id'],
                'name': group['name'],
                'description': group['description'],
                'word_count': group['word_count']
            } for group in groups])

        except Exception as e:
            logger.error(f"Error fetching word groups: {str(e)}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/word-groups/<int:group_id>/words', methods=['GET'])
    @cross_origin()
    def get_words_in_group(group_id):
        try:
            cursor = app.db.cursor()
            cursor.execute('''
                SELECT 
                    w.id,
                    w.german,
                    w.english,
                    w.word_type,
                    wga.created_at
                FROM words w
                JOIN word_group_assignments wga ON w.id = wga.word_id
                WHERE wga.word_group_id = ?
                ORDER BY wga.created_at DESC
            ''', (group_id,))
            
            words = cursor.fetchall()
            return jsonify([{
                'id': word['id'],
                'german': word['german'],
                'english': word['english'],
                'word_type': word['word_type'],
                'created_at': word['created_at']
            } for word in words])

        except Exception as e:
            logger.error(f"Error fetching words in group {group_id}: {str(e)}")
            return jsonify({"error": str(e)}), 500
