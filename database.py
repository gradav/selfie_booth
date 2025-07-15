#!/usr/bin/env python3
"""
Database module for Selfie Booth application
Handles SQLite database operations and session management
"""

import sqlite3
import secrets
from datetime import datetime, timedelta


class SessionManager:
    """Manages database sessions and operations"""
    
    def __init__(self, db_path='selfie_booth.db'):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Initialize database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE,
                phone TEXT,
                first_name TEXT,
                email TEXT,
                verification_code TEXT,
                verified BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                photo_path TEXT,
                photo_data TEXT,
                photo_ready BOOLEAN DEFAULT FALSE
            )
        ''')
        conn.commit()
        conn.close()
    
    def cleanup_old_sessions(self):
        """Remove sessions older than 30 minutes to prevent database buildup"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Delete sessions older than 30 minutes
        thirty_minutes_ago = datetime.now() - timedelta(minutes=30)
        cursor.execute('''
            SELECT COUNT(*) FROM sessions WHERE created_at < ?
        ''', (thirty_minutes_ago.isoformat(),))
        old_count = cursor.fetchone()[0]
        
        if old_count > 0:
            cursor.execute('''
                DELETE FROM sessions WHERE created_at < ?
            ''', (thirty_minutes_ago.isoformat(),))
            
            deleted_count = cursor.rowcount
            conn.commit()
            print(f"🧹 Cleaned up {deleted_count} old sessions (older than 30 minutes)")
        
        conn.close()
    
    def create_session(self, first_name, phone, email, verification_code):
        """Create a new session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        session_id = secrets.token_urlsafe(16)
        current_time = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT OR REPLACE INTO sessions (session_id, phone, first_name, email, verification_code, verified, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (session_id, phone, first_name, email, verification_code, False, current_time))
        
        conn.commit()
        conn.close()
        
        return session_id
    
    def get_session_by_id(self, session_id):
        """Get session by session ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM sessions WHERE session_id = ?', (session_id,))
        result = cursor.fetchone()
        conn.close()
        return result
    
    def get_verified_session(self):
        """Get the most recent verified session ready for photo"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT first_name, session_id, created_at FROM sessions 
            WHERE verified = 1 AND (photo_ready = 0 OR photo_ready IS NULL)
            ORDER BY created_at DESC 
            LIMIT 1
        ''')
        result = cursor.fetchone()
        conn.close()
        return result
    
    def get_unverified_session(self):
        """Get the most recent unverified session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT first_name, verification_code, created_at FROM sessions 
            WHERE verified = 0 OR verified = FALSE
            ORDER BY created_at DESC 
            LIMIT 1
        ''')
        result = cursor.fetchone()
        conn.close()
        return result
    
    def verify_session(self, session_id, verification_code):
        """Verify a session with the provided code"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT verification_code, first_name FROM sessions 
            WHERE session_id = ? AND verification_code = ?
        ''', (session_id, verification_code))
        
        result = cursor.fetchone()
        
        if result:
            cursor.execute('''
                UPDATE sessions SET verified = 1 WHERE session_id = ?
            ''', (session_id,))
            conn.commit()
            conn.close()
            return True, result[1]  # Return success and first name
        else:
            conn.close()
            return False, None
    
    def update_photo_data(self, session_id, photo_data_b64):
        """Update session with photo data and mark as ready"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE sessions 
            SET photo_data = ?, photo_ready = 1 
            WHERE session_id = ?
        ''', (photo_data_b64, session_id))
        conn.commit()
        conn.close()
    
    def get_photo_data(self, session_id):
        """Get photo data for a session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT photo_ready, photo_data FROM sessions WHERE session_id = ?', (session_id,))
        result = cursor.fetchone()
        conn.close()
        return result
    
    def get_session_data(self, session_id):
        """Get full session data including photo"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT phone, first_name, email, photo_data FROM sessions WHERE session_id = ?
        ''', (session_id,))
        result = cursor.fetchone()
        conn.close()
        return result
    
    def reset_photo_for_retake(self, session_id):
        """Reset photo status for retake"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE sessions 
            SET photo_ready = 0, photo_data = NULL, photo_path = NULL 
            WHERE session_id = ?
        ''', (session_id,))
        conn.commit()
        conn.close()
    
    def delete_session(self, session_id):
        """Delete a completed session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM sessions WHERE session_id = ?', (session_id,))
        conn.commit()
        conn.close()
    
    def reset_all_sessions(self):
        """Reset all sessions (for debugging)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM sessions')
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        return deleted_count
    
    def get_session_stats(self):
        """Get session statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM sessions')
        total_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM sessions WHERE verified = 1 OR verified = TRUE')
        verified_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM sessions WHERE verified = 0 OR verified = FALSE')
        unverified_count = cursor.fetchone()[0]
        
        conn.close()
        return total_count, verified_count, unverified_count
    
    def get_recent_sessions(self, limit=10):
        """Get recent sessions for debugging"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT session_id, first_name, phone, verified, verification_code, photo_ready, created_at 
            FROM sessions 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (limit,))
        results = cursor.fetchall()
        conn.close()
        return results
    
    def get_all_sessions_debug(self):
        """Get all sessions for debugging"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT session_id, first_name, verified, created_at FROM sessions ORDER BY created_at DESC')
        results = cursor.fetchall()
        conn.close()
        return results