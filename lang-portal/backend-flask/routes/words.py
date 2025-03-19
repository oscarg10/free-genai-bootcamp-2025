from flask import request, jsonify, g, make_response, abort
from flask_cors import cross_origin
import json
import math

def load(app):
    # Endpoint: GET /words with pagination and filtering
    @app.route('/words', methods=['GET'])
    @cross_origin()
    def get_words():
        try:
            cursor = app.db.cursor()
            
            # Get query parameters
            page = max(1, int(request.args.get('page', 1)))
            words_per_page = 50
            offset = (page - 1) * words_per_page
            word_type = request.args.get('word_type')  # Filter by word type
            sort_by = request.args.get('sort_by', 'german')
            order = request.args.get('order', 'asc')
            show_practice = request.args.get('show_practice', 'true').lower() == 'true'

            # Validate parameters
            valid_columns = ['german', 'english', 'article', 'word_type', 'times_incorrect']
            valid_types = ['noun', 'verb', 'adjective']
            
            if sort_by not in valid_columns:
                sort_by = 'german'
            if order not in ['asc', 'desc']:
                order = 'asc'

            # Build the query for regular words
            words_query = '''
                SELECT 
                    'regular' as source,
                    w.id,
                    w.german,
                    w.pronunciation,
                    w.english,
                    w.article,
                    w.word_type,
                    w.additional_info,
                    COALESCE(r.correct_count, 0) AS correct_count,
                    COALESCE(r.wrong_count, 0) AS wrong_count
                FROM words w
                LEFT JOIN word_reviews r ON w.id = r.word_id
                WHERE 1=1
            '''
            params = []

            # Add word type filter if specified
            if word_type and word_type in valid_types:
                words_query += ' AND w.word_type = ?'
                params.append(word_type)

            # Build the query for practice words
            practice_query = '''
                SELECT 
                    'practice' as source,
                    pw.id,
                    pw.german_word as german,
                    NULL as pronunciation,
                    pw.english_translation as english,
                    CASE 
                        WHEN pw.german_word LIKE 'der %' THEN 'der'
                        WHEN pw.german_word LIKE 'die %' THEN 'die'
                        WHEN pw.german_word LIKE 'das %' THEN 'das'
                        ELSE NULL 
                    END as article,
                    pw.word_type,
                    NULL as additional_info,
                    0 as correct_count,
                    pw.times_incorrect as wrong_count
                FROM practice_words pw
                WHERE 1=1
            '''

            if word_type and word_type in valid_types:
                practice_query += ' AND pw.word_type = ?'
                params.append(word_type)

            # Combine queries with UNION ALL
            query = f'''
                {words_query}
                UNION ALL
                {practice_query}
                ORDER BY {sort_by} {order}
                LIMIT ? OFFSET ?
            '''
            params.extend([words_per_page, offset])

            app.logger.info(f"Executing query: {query} with params: {params}")
            
            # Execute query
            cursor.execute(query, tuple(params))
            words = cursor.fetchall()
            app.logger.info(f"Found {len(words)} words")

            # Get total count with filters
            count_query = '''
                SELECT (
                    SELECT COUNT(*) FROM words w WHERE 1=1
                    {word_type_filter1}
                ) + (
                    SELECT COUNT(*) FROM practice_words pw WHERE 1=1
                    {word_type_filter2}
                )
            '''.format(
                word_type_filter1=' AND word_type = ?' if word_type and word_type in valid_types else '',
                word_type_filter2=' AND word_type = ?' if word_type and word_type in valid_types else ''
            )
            count_params = []
            if word_type and word_type in valid_types:
                count_params.extend([word_type, word_type])

            cursor.execute(count_query, tuple(count_params))
            total_words = cursor.fetchone()[0]
            total_pages = (total_words + words_per_page - 1) // words_per_page

            # Format response
            words_data = []
            for word in words:
                try:
                    word_dict = {
                        'source': word[0],
                        'id': word[1],
                        'german': word[2],
                        'pronunciation': word[3],
                        'english': word[4],
                        'article': word[5],
                        'word_type': word[6],
                        'additional_info': json.loads(word[7]) if word[7] else {},
                        'correct_count': word[8],
                        'wrong_count': word[9]
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
                        'words_per_page': words_per_page,
                        'total_words': total_words
                    }
                }
            })

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

    # Create a new word
    @app.route('/words', methods=['POST'])
    @cross_origin()
    def create_word():
        try:
            data = request.get_json()
            
            # Validate required fields
            required_fields = ['german', 'english', 'word_type']
            for field in required_fields:
                if field not in data:
                    return make_response({
                        'status': 'error',
                        'message': f'Missing required field: {field}'
                    }, 400)
            
            # Validate word type
            valid_types = ['noun', 'verb', 'adjective']
            if data['word_type'] not in valid_types:
                return make_response({
                    'status': 'error',
                    'message': f'Invalid word type. Must be one of: {", ".join(valid_types)}'
                }, 400)
            
            # Prepare additional info as JSON
            additional_info = data.get('additional_info', {})
            if isinstance(additional_info, dict):
                additional_info_json = json.dumps(additional_info)
            else:
                additional_info_json = '{}'
            
            cursor = app.db.cursor()
            cursor.execute('''
                INSERT INTO words (german, english, pronunciation, article, word_type, additional_info)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                data['german'],
                data['english'],
                data.get('pronunciation', ''),
                data.get('article', ''),
                data['word_type'],
                additional_info_json
            ))
            
            word_id = cursor.lastrowid
            app.db.commit()
            
            # Return the created word
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
            }, 201)
            
        except Exception as e:
            app.logger.error(f"Error creating word: {str(e)}")
            return make_response({
                'status': 'error',
                'message': f'Failed to create word: {str(e)}'
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