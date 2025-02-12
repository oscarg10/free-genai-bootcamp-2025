from flask import request, jsonify, g, make_response, abort
from flask_cors import cross_origin
import json

def load(app):
    # Endpoint: GET /words with pagination and filtering
    @app.route('/words', methods=['GET'])
    @cross_origin()
    def get_words():
        try:
            cursor = app.db.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='words'")
            if not cursor.fetchone():
                app.logger.error("Words table does not exist")
                return make_response({
                    'status': 'error',
                    'message': 'Database not properly initialized'
                }, 500)

            # Get query parameters
            page = max(1, int(request.args.get('page', 1)))
            words_per_page = 50
            offset = (page - 1) * words_per_page
            word_type = request.args.get('word_type')  # Filter by word type
            sort_by = request.args.get('sort_by', 'german')
            order = request.args.get('order', 'asc')

            # Validate parameters
            valid_columns = ['german', 'english', 'article', 'word_type', 'correct_count', 'wrong_count']
            valid_types = ['noun', 'verb', 'adjective']
            
            if sort_by not in valid_columns:
                sort_by = 'german'
            if order not in ['asc', 'desc']:
                order = 'asc'

            # Build the query
            query = '''
                SELECT w.id, w.german, w.pronunciation, w.english, w.article, 
                       w.word_type, w.additional_info,
                       COALESCE(r.correct_count, 0) AS correct_count,
                       COALESCE(r.wrong_count, 0) AS wrong_count
                FROM words w
                LEFT JOIN word_reviews r ON w.id = r.word_id
                WHERE 1=1
            '''
            params = []

            # Add word type filter if specified
            if word_type and word_type in valid_types:
                query += ' AND w.word_type = ?'
                params.append(word_type)

            # Add sorting and pagination
            query += f' ORDER BY {sort_by} {order} LIMIT ? OFFSET ?'
            params.extend([words_per_page, offset])

            app.logger.info(f"Executing query: {query} with params: {params}")
            
            # Execute query
            cursor.execute(query, tuple(params))
            words = cursor.fetchall()
            app.logger.info(f"Found {len(words)} words")

            # Get total count with filters
            count_query = 'SELECT COUNT(*) FROM words WHERE 1=1'
            count_params = []
            if word_type and word_type in valid_types:
                count_query += ' AND word_type = ?'
                count_params.append(word_type)

            cursor.execute(count_query, tuple(count_params))
            total_words = cursor.fetchone()[0]
            total_pages = (total_words + words_per_page - 1) // words_per_page

            # Format response
            words_data = []
            for word in words:
                try:
                    word_dict = {
                        'id': word[0],
                        'german': word[1],
                        'pronunciation': word[2],
                        'english': word[3],
                        'article': word[4],
                        'word_type': word[5],
                        'additional_info': json.loads(word[6]) if word[6] else {},
                        'correct_count': word[7],
                        'wrong_count': word[8]
                    }
                    words_data.append(word_dict)
                except Exception as e:
                    app.logger.error(f"Error processing word: {word}, error: {str(e)}")

            return make_response({
                'status': 'success',
                'data': {
                    'words': words_data,
                    'pagination': {
                        'current_page': page,
                        'total_pages': total_pages,
                        'total_words': total_words,
                        'words_per_page': words_per_page
                    }
                }
            }, 200)

        except ValueError as e:
            app.logger.error(f"Invalid parameter: {str(e)}")
            return make_response({
                'status': 'error',
                'message': 'Invalid parameters provided'
            }, 400)
        except Exception as e:
            app.logger.error(f"Error fetching words: {str(e)}")
            return make_response({
                'status': 'error',
                'message': f'Internal server error: {str(e)}'
            }, 500)

    # Get word by ID
    @app.route('/words/<int:word_id>', methods=['GET'])
    @cross_origin()
    def get_word(word_id):
        try:
            cursor = app.db.cursor()
            cursor.execute('''
                SELECT w.id, w.german, w.pronunciation, w.english, w.article, 
                       w.word_type, w.additional_info,
                       COALESCE(r.correct_count, 0) AS correct_count,
                       COALESCE(r.wrong_count, 0) AS wrong_count
                FROM words w
                LEFT JOIN word_reviews r ON w.id = r.word_id
                WHERE w.id = ?
            ''', (word_id,))
            
            word = cursor.fetchone()
            if not word:
                return make_response({
                    'status': 'error',
                    'message': 'Word not found'
                }, 404)

            word_data = {
                'id': word[0],
                'german': word[1],
                'pronunciation': word[2],
                'english': word[3],
                'article': word[4],
                'word_type': word[5],
                'additional_info': json.loads(word[6]) if word[6] else {},
                'correct_count': word[7],
                'wrong_count': word[8]
            }

            return make_response({
                'status': 'success',
                'data': word_data
            }, 200)

        except Exception as e:
            app.logger.error(f"Error fetching word {word_id}: {str(e)}")
            return make_response({
                'status': 'error',
                'message': f'Internal server error: {str(e)}'
            }, 500)