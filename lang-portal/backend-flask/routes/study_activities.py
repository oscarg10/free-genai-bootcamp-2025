from flask import jsonify, request
from flask_cors import cross_origin
import math
import requests
import sqlite3
import logging
import os

logger = logging.getLogger(__name__)

# Constants
SONG_VOCAB_URL = 'http://localhost:8000'

def proxy_to_song_vocab(method, endpoint, json=None, params=None):
    """Proxy a request to the song-vocab service.
    
    Args:
        method: HTTP method (GET, POST, etc.)
        endpoint: API endpoint
        json: Optional JSON body
        params: Optional query parameters
        
    Returns:
        Response from song-vocab service
        
    Raises:
        Exception: If the request fails
    """
    try:
        url = f"{SONG_VOCAB_URL}{endpoint}"
        response = requests.request(
            method=method,
            url=url,
            json=json,
            params=params
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error proxying to song-vocab: {str(e)}")
        raise

def get_activity_type(url: str) -> str:
    """Determine activity type based on URL pattern."""
    if 'localhost:7860' in url:
        return 'writing'
    elif 'localhost:8000' in url:
        return 'song'
    elif 'localhost:8501' in url:
        return 'listening'
    else:
        return 'typing'

def update_activity_url(app, activity_name: str, new_url: str):
    """Update the URL of a study activity using proper SQLite3 practices."""
    with app.db as conn:
        try:
            conn.execute("BEGIN TRANSACTION")
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE study_activities SET url = ? WHERE name = ?",
                (new_url, activity_name)
            )
            conn.commit()
            logger.info(f"Updated URL for {activity_name} to {new_url}")
        except Exception as e:
            conn.rollback()
            logger.error(f"Error updating activity URL: {str(e)}")
            raise e
        finally:
            cursor.close()

def load(app):

    @app.route('/api/debug/db', methods=['GET'])
    @cross_origin()
    def debug_db():
        try:
            # Test database connection
            cursor = app.db.cursor()
            
            # Get database path
            db_path = os.path.abspath(app.db.database)
            logger.info(f"Database path: {db_path}")
            
            # Test study_activities table
            cursor.execute('SELECT * FROM study_activities')
            activities = [dict(row) for row in cursor.fetchall()]
            
            # Test groups table
            cursor.execute('SELECT * FROM groups')
            groups = [dict(row) for row in cursor.fetchall()]
            
            return jsonify({
                'database_path': db_path,
                'database_exists': os.path.exists(db_path),
                'study_activities': activities,
                'groups': groups
            })
        except Exception as e:
            logger.error(f"Debug endpoint error: {str(e)}")
            return jsonify({'error': str(e)}), 500
            
    @app.route('/api/study-activities', methods=['GET'])
    @cross_origin()
    def get_study_activities():
        cursor = app.db.cursor()
        cursor.execute('SELECT id, name, url, preview_url FROM study_activities')
        activities = cursor.fetchall()
        
        return jsonify([{
            'id': activity['id'],
            'title': activity['name'],
            'launch_url': activity['url'],
            'preview_url': activity['preview_url'],
            'activity_type': get_activity_type(activity['url'])
        } for activity in activities])

    @app.route('/api/study-activities/<int:id>', methods=['GET'])
    @cross_origin()
    def get_study_activity(id):
        cursor = app.db.cursor()
        cursor.execute('SELECT id, name, url, preview_url FROM study_activities WHERE id = ?', (id,))
        activity = cursor.fetchone()
        
        if not activity:
            return jsonify({'error': 'Activity not found'}), 404
            
        return jsonify({
            'id': activity['id'],
            'title': activity['name'],
            'launch_url': activity['url'],
            'preview_url': activity['preview_url'],
            'activity_type': get_activity_type(activity['url'])
        })

    @app.route('/api/study-activities/<int:id>/sessions', methods=['GET'])
    @cross_origin()
    def get_study_activity_sessions(id):
        cursor = app.db.cursor()
        
        # Verify activity exists
        cursor.execute('SELECT id FROM study_activities WHERE id = ?', (id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Activity not found'}), 404

        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        offset = (page - 1) * per_page

        # Get total count
        cursor.execute('''
            SELECT COUNT(*) as count 
            FROM study_sessions ss
            JOIN groups g ON g.id = ss.group_id
            WHERE ss.study_activity_id = ?
        ''', (id,))
        total_count = cursor.fetchone()['count']

        # Get paginated sessions
        cursor.execute('''
            SELECT 
                ss.id,
                ss.group_id,
                g.name as group_name,
                sa.name as activity_name,
                ss.created_at,
                ss.study_activity_id as activity_id,
                COUNT(wri.id) as review_items_count
            FROM study_sessions ss
            JOIN groups g ON g.id = ss.group_id
            JOIN study_activities sa ON sa.id = ss.study_activity_id
            LEFT JOIN word_review_items wri ON wri.study_session_id = ss.id
            WHERE ss.study_activity_id = ?
            GROUP BY ss.id, ss.group_id, g.name, sa.name, ss.created_at, ss.study_activity_id
            ORDER BY ss.created_at DESC
            LIMIT ? OFFSET ?
        ''', (id, per_page, offset))
        sessions = cursor.fetchall()

        return jsonify({
            'items': [{
                'id': session['id'],
                'group_id': session['group_id'],
                'group_name': session['group_name'],
                'activity_id': session['activity_id'],
                'activity_name': session['activity_name'],
                'start_time': session['created_at'],
                'end_time': session['created_at'],  # For now, just use the same time since we don't track end time
                'review_items_count': session['review_items_count']
            } for session in sessions],
            'total': total_count,
            'page': page,
            'per_page': per_page,
            'total_pages': math.ceil(total_count / per_page)
        })

    @app.route('/api/study-activities/<int:id>/launch', methods=['GET'])
    @cross_origin()
    def get_study_activity_launch_data(id):
        cursor = app.db.cursor()
        
        try:
            # Get activity details
            cursor.execute('SELECT id, name, url, preview_url FROM study_activities WHERE id = ?', (id,))
            activity = cursor.fetchone()
            
            if not activity:
                return jsonify({'error': 'Activity not found'}), 404

            activity_type = get_activity_type(activity['url'])
            response = {
                'activity': {
                    'id': activity['id'],
                    'title': activity['name'],
                    'launch_url': activity['url'],
                    'preview_url': activity['preview_url'],
                    'activity_type': activity_type
                }
            }
            
            # Only fetch groups for typing activity
            if activity_type == 'typing':
                cursor.execute('SELECT id, name FROM groups')
                groups = cursor.fetchall()
                response['groups'] = [{
                    'id': group['id'],
                    'name': group['name']
                } for group in groups]
        
            return jsonify(response)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/study-activities/words', methods=['GET'])
    @cross_origin()
    def get_study_activity_words():
        try:
            # Get group_id from query parameters, default to group 1
            group_id = request.args.get('group_id', '1')
            try:
                group_id = int(group_id)
            except (TypeError, ValueError):
                return jsonify({'error': 'group_id must be a number'}), 400

            # Get words for the group using proper transaction handling
            with app.db.get() as connection:
                cursor = connection.cursor()
                try:
                    # Begin transaction
                    connection.execute('BEGIN TRANSACTION')

                    # First check if the group exists
                    cursor.execute(
                        'SELECT id FROM groups WHERE id = ?',
                        (group_id,)
                    )
                    if not cursor.fetchone():
                        connection.rollback()
                        return jsonify({'error': 'Group not found'}), 404

                    # Get words for the group
                    cursor.execute('''
                        SELECT w.* FROM words w
                        JOIN word_groups gw ON w.id = gw.word_id
                        WHERE gw.group_id = ?
                    ''', (group_id,))
                    words = cursor.fetchall()

                    # Commit transaction
                    connection.commit()
                except Exception as e:
                    connection.rollback()
                    raise e
                finally:
                    cursor.close()

            if not words:
                return jsonify({'error': 'No words found for this group'}), 404

            return jsonify({
                'words': [{
                    'id': word['id'],
                    'german': word['german'],
                    'english': word['english'],
                    'word_type': word['word_type'],
                    'article': word['article'],
                    'pronunciation': word['pronunciation']
                } for word in words]
            })
        except Exception as e:
            app.logger.error(f"Error fetching words: {str(e)}")
            return jsonify({'error': str(e)}), 500
            
    @app.route('/api/study-activities/<int:id>/songs', methods=['GET'])
    @cross_origin()
    def get_study_activity_songs(id):
        try:
            # Verify activity exists
            cursor = app.db.cursor()
            cursor.execute('SELECT id FROM study_activities WHERE id = ?', (id,))
            if not cursor.fetchone():
                return jsonify({'error': 'Activity not found'}), 404

            # Get pagination parameters
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)
            
            # Get all study sessions for this activity
            cursor.execute('''
                SELECT id FROM study_sessions 
                WHERE study_activity_id = ?
            ''', (id,))
            sessions = cursor.fetchall()
            
            if not sessions:
                return jsonify({
                    'items': [],
                    'total': 0,
                    'page': page,
                    'per_page': per_page,
                    'total_pages': 0
                })
            
            # Get songs from song-vocab service
            session_ids = [session['id'] for session in sessions]
            try:
                response = proxy_to_song_vocab(
                    'GET',
                    '/api/songs',
                    params={
                        'session_ids': ','.join(map(str, session_ids)),
                        'page': page,
                        'per_page': per_page
                    }
                )
                return jsonify(response)
            except Exception as e:
                logger.error(f"Error fetching songs from song-vocab: {str(e)}")
                return jsonify({'error': 'Failed to fetch songs'}), 500
            
        except Exception as e:
            logger.error(f"Error in get_study_activity_songs: {str(e)}")
            return jsonify({'error': str(e)}), 500
            
    @app.route('/api/study-activities/<int:id>/songs/<string:song_id>/vocabulary', methods=['GET'])
    @cross_origin()
    def get_song_vocabulary(id, song_id):
        try:
            # Verify activity exists
            cursor = app.db.cursor()
            cursor.execute('SELECT id FROM study_activities WHERE id = ?', (id,))
            if not cursor.fetchone():
                return jsonify({'error': 'Activity not found'}), 404

            # Get study sessions for this activity
            cursor.execute('''
                SELECT id FROM study_sessions 
                WHERE study_activity_id = ?
            ''', (id,))
            sessions = cursor.fetchall()
            
            if not sessions:
                return jsonify({'error': 'No sessions found'}), 404
            
            # Get vocabulary from song-vocab service
            session_ids = [session['id'] for session in sessions]
            try:
                response = proxy_to_song_vocab(
                    'GET',
                    f'/api/songs/{song_id}/vocabulary',
                    params={'session_ids': ','.join(map(str, session_ids))}
                )
                return jsonify(response)
            except Exception as e:
                logger.error(f"Error fetching vocabulary from song-vocab: {str(e)}")
                return jsonify({'error': 'Failed to fetch vocabulary'}), 500
            
        except Exception as e:
            logger.error(f"Error in get_song_vocabulary: {str(e)}")
            return jsonify({'error': str(e)}), 500
            
    @app.route('/api/study-activities/<int:id>/songs/process', methods=['POST'])
    @cross_origin()
    def process_song(id):
        try:
            # Log request details
            logger.info(f"Processing song request for activity {id}")
            logger.info(f"Request data: {request.get_json()}")
            
            # Validate request data
            data = request.get_json()
            if not data:
                logger.error("No JSON data in request")
                return jsonify({'error': 'Request must contain JSON data'}), 400
                
            required_fields = ['song_title', 'artist', 'group_id']
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                logger.error(f"Missing required fields: {missing_fields}")
                return jsonify({'error': f"Missing required fields: {', '.join(missing_fields)}"}), 400
            
            # Verify database connection
            db_path = os.path.abspath(app.db.database)
            if not os.path.exists(db_path):
                logger.error(f"Database not found at {db_path}")
                return jsonify({'error': 'Database connection error'}), 500
            
            # Begin transaction
            cursor = app.db.cursor()
            
            try:
                # Verify activity exists
                logger.info(f"Verifying activity {id} exists")
                cursor.execute('SELECT * FROM study_activities WHERE id = ?', (id,))
                activity = cursor.fetchone()
                
                if not activity:
                    logger.warning(f"Activity {id} not found")
                    return jsonify({'error': 'Activity not found'}), 404
                    
                # Verify group exists
                logger.info(f"Verifying group {data['group_id']} exists")
                cursor.execute('SELECT * FROM groups WHERE id = ?', (data['group_id'],))
                group = cursor.fetchone()
                
                if not group:
                    logger.warning(f"Group {data['group_id']} not found")
                    return jsonify({'error': 'Group not found'}), 404

                # Create study session
                logger.info("Creating study session")
                cursor.execute('''
                    INSERT INTO study_sessions 
                    (group_id, study_activity_id) 
                    VALUES (?, ?)
                ''', (data['group_id'], id))
                session_id = cursor.lastrowid
                logger.info(f"Created study session with id {session_id}")
                
                # Process song in song-vocab service
                try:
                    logger.info("Sending request to song-vocab service")
                    payload = {
                        'song_title': data['song_title'],
                        'artist': data['artist'],
                        'study_activity_id': id,
                        'external_session_id': session_id
                    }
                    logger.info(f"song-vocab payload: {payload}")
                    
                    response = proxy_to_song_vocab(
                        'POST',
                        '/api/agent',
                        json=payload
                    )
                    
                    # Validate song-vocab response
                    if response.get('error'):
                        logger.error(f"song-vocab error: {response['error']}")
                        app.db.get().rollback()
                        return jsonify({'error': 'Song processing failed'}), 500
                        
                    # Only commit if song-vocab request succeeds
                    logger.info("song-vocab request successful, committing transaction")
                    app.db.commit()
                    
                    # Log vocabulary results
                    vocab_count = len(response.get('vocabulary', []))
                    logger.info(f"Processed song with {vocab_count} vocabulary items")
                    
                    return jsonify(response)
                    
                except requests.exceptions.RequestException as e:
                    # Handle network/connection errors
                    app.db.get().rollback()
                    logger.error(f"Network error with song-vocab service: {str(e)}")
                    return jsonify({'error': 'Could not connect to song processing service'}), 503
                    
                except Exception as e:
                    # Handle unexpected errors
                    app.db.get().rollback()
                    logger.error(f"Unexpected error processing song: {str(e)}")
                    return jsonify({'error': 'Internal server error'}), 500
                    
            except sqlite3.IntegrityError as e:
                # Handle database constraint violations
                logger.error(f"Database integrity error: {str(e)}")
                return jsonify({'error': 'Database constraint violation'}), 409
                
            except Exception as e:
                # Handle unexpected database errors
                logger.error(f"Unexpected database error: {str(e)}")
                return jsonify({'error': 'Database error'}), 500
                
            finally:
                cursor.close()
                    
        except Exception as e:
            logger.error(f"Error in process_song: {str(e)}")
            return jsonify({'error': str(e)}), 500