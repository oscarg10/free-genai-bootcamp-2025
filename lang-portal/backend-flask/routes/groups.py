from flask import request, jsonify, g
from flask_cors import cross_origin
import json
import sqlite3
import logging

logger = logging.getLogger(__name__)

def load(app):
  @app.route('/api/groups', methods=['GET'])
  @cross_origin()
  def get_groups():
    try:
      cursor = app.db.cursor()

      # Get the current page number from query parameters (default is 1)
      page = int(request.args.get('page', 1))
      groups_per_page = 10
      offset = (page - 1) * groups_per_page

      # Get sorting parameters from the query string
      sort_by = request.args.get('sort_by', 'name')  # Default to sorting by 'name'
      order = request.args.get('order', 'asc')  # Default to ascending order

      # Validate sort_by and order
      valid_columns = ['name', 'words_count']
      if sort_by not in valid_columns:
        sort_by = 'name'
      if order not in ['asc', 'desc']:
        order = 'asc'

      # Query to fetch groups with sorting and the cached word count
      query = '''
        SELECT id, name, words_count
        FROM groups
        ORDER BY {} {}
        LIMIT ? OFFSET ?
      '''.format(
        'name' if sort_by == 'name' else 'words_count',
        'ASC' if order.upper() == 'ASC' else 'DESC'
      )
      
      try:
        # Query groups
        cursor.execute(query, (groups_per_page, offset))
        groups = [dict(row) for row in cursor.fetchall()]

        # Query total count
        cursor.execute('SELECT COUNT(*) FROM groups')
        total_groups = cursor.fetchone()[0]
        total_pages = (total_groups + groups_per_page - 1) // groups_per_page
      except sqlite3.Error as e:
        logger.error(f'Database error: {e}')
        return jsonify({'error': 'Database error occurred'}), 500

      # Format the response
      groups_data = [{
        "id": group["id"],
        "group_name": group["name"],
        "word_count": group["words_count"]
      } for group in groups]

      # Return groups and pagination metadata
      return jsonify({
        'groups': groups_data,
        'total_pages': total_pages,
        'current_page': page
      })
    except Exception as e:
      return jsonify({"error": str(e)}), 500

  @app.route('/api/groups', methods=['POST'])
  @cross_origin()
  def create_group():
    try:
      data = request.get_json()
      
      if not data or 'name' not in data:
        return jsonify({"error": "Group name is required"}), 400
      
      group_name = data['name'].strip()
      if not group_name:
        return jsonify({"error": "Group name cannot be empty"}), 400

      # Check if a group with this name  already exists
      cursor = app.db.cursor()
      cursor.execute('SELECT id FROM groups WHERE name = ?', (group_name,))
      existing_group = cursor.fetchone()
      
      if existing_group:
        return jsonify({"error": "A group with this name already exists"}), 409

      # Create the new group
      cursor.execute('''
        INSERT INTO groups (name, words_count) 
        VALUES (?, 0)
      ''', (group_name,))
      
      group_id = cursor.lastrowid
      app.db.commit()

      # Return the created group
      return jsonify({
        "id": group_id,
        "group_name": group_name,
        "word_count": 0
      }), 201

    except Exception as e:
      app.db.rollback()
      return jsonify({"error": str(e)}), 500

  @app.route('/api/groups/<int:id>', methods=['GET'])
  @cross_origin()
  def get_group(id):
    try:
      cursor = app.db.cursor()

      # Get group details
      cursor.execute('''
        SELECT id, name, words_count
        FROM groups
        WHERE id = ?
      ''', (id,))
      
      group = cursor.fetchone()
      if not group:
        return jsonify({"error": "Group not found"}), 404

      return jsonify({
        "id": group["id"],
        "group_name": group["name"],
        "word_count": group["words_count"]
      })
    except Exception as e:
      return jsonify({"error": str(e)}), 500

  @app.route('/api/groups/<int:id>/words', methods=['GET'])
  @cross_origin()
  def get_group_words(id):
    try:
      cursor = app.db.cursor()
      
      # Get pagination parameters
      page = int(request.args.get('page', 1))
      words_per_page = 10
      offset = (page - 1) * words_per_page

      # Get sorting parameters
      sort_by = request.args.get('sort_by', 'german')
      order = request.args.get('order', 'asc')

      # Validate sort parameters
      valid_columns = ['german', 'english', 'word_type', 'article', 'correct_count', 'wrong_count']
      if sort_by not in valid_columns:
        sort_by = 'german'
      if order not in ['asc', 'desc']:
        order = 'asc'

      # First, check if the group exists
      cursor.execute('SELECT name FROM groups WHERE id = ?', (id,))
      group = cursor.fetchone()
      if not group:
        return jsonify({"error": "Group not found"}), 404

      # Query to fetch words with pagination and sorting
      cursor.execute(f'''
        SELECT w.*, 
               COALESCE(wr.correct_count, 0) as correct_count,
               COALESCE(wr.wrong_count, 0) as wrong_count
        FROM words w
        JOIN word_groups wg ON w.id = wg.word_id
        LEFT JOIN word_reviews wr ON w.id = wr.word_id
        WHERE wg.group_id = ?
        ORDER BY {sort_by} {order}
        LIMIT ? OFFSET ?
      ''', (id, words_per_page, offset))
      
      words = cursor.fetchall()

      # Get total words count for pagination
      cursor.execute('''
        SELECT COUNT(*) 
        FROM word_groups 
        WHERE group_id = ?
      ''', (id,))
      total_words = cursor.fetchone()[0]
      total_pages = (total_words + words_per_page - 1) // words_per_page

      # Format the response
      words_data = []
      for word in words:
        words_data.append({
          "id": word["id"],
          "german": word["german"],
          "english": word["english"],
          "word_type": word["word_type"],
          "article": word["article"],
          "correct_count": word["correct_count"],
          "wrong_count": word["wrong_count"]
        })

      return jsonify({
        'words': words_data,
        'total_pages': total_pages,
        'current_page': page
      })
    except Exception as e:
      return jsonify({"error": str(e)}), 500

  # todo GET /api/groups/:id/words/raw

  @app.route('/api/groups/<int:id>/study_sessions', methods=['GET'])
  @cross_origin()
  def get_group_study_sessions(id):
    try:
      cursor = app.db.cursor()
      
      # Get pagination parameters
      page = int(request.args.get('page', 1))
      sessions_per_page = 10
      offset = (page - 1) * sessions_per_page

      # Get sorting parameters
      sort_by = request.args.get('sort_by', 'created_at')
      order = request.args.get('order', 'desc')  # Default to newest first

      # Map frontend sort keys to database columns
      sort_mapping = {
        'startTime': 'created_at',
        'endTime': 'last_activity_time',
        'activityName': 'a.name',
        'groupName': 'g.name',
        'reviewItemsCount': 'review_count'
      }

      # Use mapped sort column or default to created_at
      sort_column = sort_mapping.get(sort_by, 'created_at')

      # Get total count for pagination
      cursor.execute('''
        SELECT COUNT(*)
        FROM study_sessions
        WHERE group_id = ?
      ''', (id,))
      total_sessions = cursor.fetchone()[0]
      total_pages = (total_sessions + sessions_per_page - 1) // sessions_per_page

      # Get study sessions for this group with dynamic calculations
      cursor.execute(f'''
        SELECT 
          s.id,
          s.group_id,
          s.study_activity_id,
          s.created_at as start_time,
          (
            SELECT MAX(created_at)
            FROM word_review_items
            WHERE study_session_id = s.id
          ) as last_activity_time,
          a.name as activity_name,
          g.name as group_name,
          (
            SELECT COUNT(*)
            FROM word_review_items
            WHERE study_session_id = s.id
          ) as review_count
        FROM study_sessions s
        JOIN study_activities a ON s.study_activity_id = a.id
        JOIN groups g ON s.group_id = g.id
        WHERE s.group_id = ?
        ORDER BY {sort_column} {order}
        LIMIT ? OFFSET ?
      ''', (id, sessions_per_page, offset))
      
      sessions = cursor.fetchall()
      sessions_data = []
      
      for session in sessions:
        # If there's no last_activity_time, use start_time + 30 minutes
        end_time = session["last_activity_time"]
        if not end_time:
            end_time = cursor.execute('SELECT datetime(?, "+30 minutes")', (session["start_time"],)).fetchone()[0]
        
        sessions_data.append({
          "id": session["id"],
          "group_id": session["group_id"],
          "group_name": session["group_name"],
          "study_activity_id": session["study_activity_id"],
          "activity_name": session["activity_name"],
          "start_time": session["start_time"],
          "end_time": end_time,
          "review_items_count": session["review_count"]
        })

      return jsonify({
        'study_sessions': sessions_data,
        'total_pages': total_pages,
        'current_page': page
      })
    except Exception as e:
      return jsonify({"error": str(e)}), 500