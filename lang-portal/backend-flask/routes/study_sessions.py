from flask import request, jsonify, g, abort
from flask_cors import cross_origin
from datetime import datetime
import math

def load(app):
    @app.route('/api/study-sessions', methods=['POST'])
    @cross_origin()
    def create_study_session():
        try:
            # Extract and validate request data
            data = request.get_json()
            
            if not data:
                return jsonify({
                    'status': 'error',
                    'message': 'No JSON data provided'
                }), 400
            
            group_id = data.get('group_id')
            study_activity_id = data.get('study_activity_id')
            
            # Validate required fields
            if group_id is None:
                return jsonify({
                    'status': 'error',
                    'message': 'group_id is required'
                }), 400
                
            if study_activity_id is None:
                return jsonify({
                    'status': 'error',
                    'message': 'study_activity_id is required'
                }), 400
            
            # Validate integer types
            try:
                group_id = int(group_id)
                study_activity_id = int(study_activity_id)
            except (ValueError, TypeError):
                return jsonify({
                    'status': 'error',
                    'message': 'group_id and study_activity_id must be integers'
                }), 400

            # Database operations with proper transaction management
            cursor = app.db.cursor()
            try:
                # Validate group exists
                cursor.execute("SELECT id FROM groups WHERE id = ?", (group_id,))
                if not cursor.fetchone():
                    return jsonify({
                        'status': 'error',
                        'message': f'Group with id {group_id} does not exist'
                    }), 400

                # Validate study activity exists
                cursor.execute("SELECT id FROM study_activities WHERE id = ?", (study_activity_id,))
                if not cursor.fetchone():
                    return jsonify({
                        'status': 'error',
                        'message': f'Study activity with id {study_activity_id} does not exist'
                    }), 400

                # Insert new study session
                current_time = datetime.utcnow().isoformat()
                cursor.execute("""
                    INSERT INTO study_sessions (group_id, study_activity_id, created_at)
                    VALUES (?, ?, ?)
                """, (group_id, study_activity_id, current_time))
                
                # Get the id of the newly created session
                new_session_id = cursor.lastrowid
                
                # Fetch the created session
                cursor.execute("""
                    SELECT id, group_id, study_activity_id, created_at
                    FROM study_sessions
                    WHERE id = ?
                """, (new_session_id,))
                
                session = cursor.fetchone()
                
                # Commit the transaction
                app.db.commit()
                
                return jsonify({
                    'status': 'success',
                    'data': {
                        'id': session[0],
                        'group_id': session[1],
                        'study_activity_id': session[2],
                        'created_at': session[3]
                    }
                }), 201

            except Exception as e:
                app.db.rollback()
                raise e
            finally:
                cursor.close()
            
        except Exception as e:
            app.logger.error(f"Error creating study session: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': 'Internal server error'
            }), 500

    @app.route('/api/study-sessions', methods=['GET'])
    @cross_origin()
    def get_study_sessions():
        try:
            cursor = app.db.cursor()
            
            # Get pagination parameters
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)
            offset = (page - 1) * per_page

            # Get total count
            cursor.execute('''
                SELECT COUNT(*) 
                FROM study_sessions
            ''')
            total_count = cursor.fetchone()[0]
            total_pages = math.ceil(total_count / per_page)

            # Get paginated study sessions
            cursor.execute('''
                SELECT id, group_id, study_activity_id, created_at
                FROM study_sessions
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            ''', (per_page, offset))
            
            study_sessions = []
            for row in cursor.fetchall():
                study_sessions.append({
                    'id': row[0],
                    'group_id': row[1],
                    'study_activity_id': row[2],
                    'created_at': row[3]
                })
            
            return jsonify({
                'status': 'success',
                'data': {
                    'study_sessions': study_sessions,
                    'pagination': {
                        'total_count': total_count,
                        'total_pages': total_pages,
                        'current_page': page,
                        'per_page': per_page
                    }
                }
            }), 200
            
        except Exception as e:
            app.logger.error(f"Error fetching study sessions: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': 'Internal server error'
            }), 500