import unittest
from flask import json
from app import create_app
from datetime import datetime

class TestStudySessionsRoutes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Create tables before running any tests"""
        cls.app = create_app()
        with cls.app.app_context():
            cursor = cls.app.db.cursor()
            
            # Create groups table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            
            # Create study_activities table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS study_activities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            
            # Create study_sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS study_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_id INTEGER NOT NULL,
                    study_activity_id INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (group_id) REFERENCES groups (id),
                    FOREIGN KEY (study_activity_id) REFERENCES study_activities (id)
                )
            """)
            
            cls.app.db.commit()
    
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()
        self.db = self.app.db
        
        # Setup test data
        with self.app.app_context():
            cursor = self.db.cursor()
            # Create test group
            cursor.execute("""
                INSERT INTO groups (name, created_at)
                VALUES (?, ?)
            """, ('Test Group', datetime.utcnow().isoformat()))
            self.test_group_id = cursor.lastrowid
            
            # Create test study activity
            cursor.execute("""
                INSERT INTO study_activities (name, created_at)
                VALUES (?, ?)
            """, ('Test Activity', datetime.utcnow().isoformat()))
            self.test_activity_id = cursor.lastrowid
            
            self.db.commit()
    
    def tearDown(self):
        # Clean up test data
        with self.app.app_context():
            cursor = self.db.cursor()
            cursor.execute("DELETE FROM study_sessions")
            cursor.execute("DELETE FROM groups WHERE id = ?", (self.test_group_id,))
            cursor.execute("DELETE FROM study_activities WHERE id = ?", (self.test_activity_id,))
            self.db.commit()
    
    def test_create_study_session_success(self):
        """Test 5.1: Test successful session creation"""
        response = self.client.post('/api/study-sessions', json={
            'group_id': self.test_group_id,
            'study_activity_id': self.test_activity_id
        })
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
        self.assertIn('data', data)
        self.assertIn('id', data['data'])
        self.assertEqual(data['data']['group_id'], self.test_group_id)
        self.assertEqual(data['data']['study_activity_id'], self.test_activity_id)
    
    def test_missing_group_id(self):
        """Test 5.2: Test failure when group_id is missing"""
        response = self.client.post('/api/study-sessions', json={
            'study_activity_id': self.test_activity_id
        })
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'error')
        self.assertIn('group_id is required', data['message'])
    
    def test_missing_activity_id(self):
        """Test 5.3: Test failure when study_activity_id is missing"""
        response = self.client.post('/api/study-sessions', json={
            'group_id': self.test_group_id
        })
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'error')
        self.assertIn('study_activity_id is required', data['message'])
    
    def test_nonexistent_group(self):
        """Test 5.4: Test failure when group_id does not exist"""
        response = self.client.post('/api/study-sessions', json={
            'group_id': 99999,
            'study_activity_id': self.test_activity_id
        })
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'error')
        self.assertIn('Group with id 99999 does not exist', data['message'])
    
    def test_nonexistent_activity(self):
        """Test 5.5: Test failure when study_activity_id does not exist"""
        response = self.client.post('/api/study-sessions', json={
            'group_id': self.test_group_id,
            'study_activity_id': 99999
        })
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'error')
        self.assertIn('Study activity with id 99999 does not exist', data['message'])
    
    def test_invalid_data_types(self):
        """Test 5.6: Test failure when sending invalid data types"""
        response = self.client.post('/api/study-sessions', json={
            'group_id': "not_an_integer",
            'study_activity_id': self.test_activity_id
        })
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'error')
        self.assertIn('must be integers', data['message'])

if __name__ == '__main__':
    unittest.main()