#!/usr/bin/env python3
"""
Database module for Selfie Booth API
Handles both SQLite (development) and MySQL (production) databases
"""

import sqlite3
import secrets
from datetime import datetime, timedelta
from config_api import APIConfig

# MySQL imports with fallback
try:
    import mysql.connector
    from mysql.connector import Error
    MYSQL_AVAILABLE = True
except ImportError:
    mysql = None
    Error = Exception
    MYSQL_AVAILABLE = False


class SQLiteSessionManager:
    """SQLite session manager for development"""
    
    def __init__(self, db_path):
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
                photo_ready BOOLEAN DEFAULT FALSE,
                tablet_id TEXT,
                location TEXT
            )
        ''')
        conn.commit()
        conn.close()
        print("✅ SQLite database initialized")
    
    def cleanup_old_sessions(self):
        """Remove sessions older than configured timeout"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        timeout_minutes = APIConfig.SESSION_TIMEOUT_MINUTES
        cutoff_time = datetime.now() - timedelta(minutes=timeout_minutes)
        
        cursor.execute('''
            SELECT COUNT(*) FROM sessions WHERE created_at < ?
        ''', (cutoff_time.isoformat(),))
        old_count = cursor.fetchone()[0]
        
        if old_count > 0:
            cursor.execute('''
                DELETE FROM sessions WHERE created_at < ?
            ''', (cutoff_time.isoformat(),))
            
            deleted_count = cursor.rowcount
            conn.commit()
            if deleted_count > 0:
                print(f"🧹 Cleaned up {deleted_count} old sessions")
        
        conn.close()
    
    def create_session(self, first_name, phone, email, verification_code, tablet_id=None, location=None):
        """Create a new session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        session_id = secrets.token_urlsafe(16)
        current_time = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO sessions 
            (session_id, phone, first_name, email, verification_code, verified, created_at, tablet_id, location)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (session_id, phone, first_name, email, verification_code, False, current_time, tablet_id, location))
        
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
            return True, result[1]
        else:
            conn.close()
            return False, None
    
    def get_verified_session(self, tablet_id=None):
        """Get the most recent verified session ready for photo"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if tablet_id:
            cursor.execute('''
                SELECT first_name, session_id, created_at FROM sessions 
                WHERE verified = 1 AND (photo_ready = 0 OR photo_ready IS NULL)
                AND tablet_id = ?
                ORDER BY created_at DESC 
                LIMIT 1
            ''', (tablet_id,))
        else:
            cursor.execute('''
                SELECT first_name, session_id, created_at FROM sessions 
                WHERE verified = 1 AND (photo_ready = 0 OR photo_ready IS NULL)
                ORDER BY created_at DESC 
                LIMIT 1
            ''')
        
        result = cursor.fetchone()
        conn.close()
        return result
    
    def get_unverified_session(self, tablet_id=None):
        """Get the most recent unverified session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if tablet_id:
            cursor.execute('''
                SELECT first_name, verification_code, created_at FROM sessions 
                WHERE verified = 0 
                AND tablet_id = ?
                ORDER BY created_at DESC 
                LIMIT 1
            ''', (tablet_id,))
        else:
            cursor.execute('''
                SELECT first_name, verification_code, created_at FROM sessions 
                WHERE verified = 0
                ORDER BY created_at DESC 
                LIMIT 1
            ''')
        
        result = cursor.fetchone()
        conn.close()
        return result
    
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
        """Reset all sessions"""
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
        
        cursor.execute('SELECT COUNT(*) FROM sessions WHERE verified = 1')
        verified_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM sessions WHERE verified = 0')
        unverified_count = cursor.fetchone()[0]
        
        conn.close()
        return total_count, verified_count, unverified_count
    
    def get_recent_sessions(self, limit=10):
        """Get recent sessions for admin"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT session_id, first_name, phone, verified, verification_code, created_at,
                   photo_ready, email, photo_path, photo_data, tablet_id, location
            FROM sessions 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (limit,))
        results = cursor.fetchall()
        conn.close()
        return results
    
    def get_session_state(self, tablet_id=None):
        """Get current session state for UI updates"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check for verified session within timeout
        timeout_minutes = 3
        cutoff_time = datetime.now() - timedelta(minutes=timeout_minutes)
        
        if tablet_id:
            cursor.execute("""
                SELECT COUNT(*) FROM sessions 
                WHERE verified = 1 AND (photo_ready = 0 OR photo_ready IS NULL) 
                AND tablet_id = ? AND created_at > ?
            """, (tablet_id, cutoff_time.isoformat()))
        else:
            cursor.execute("""
                SELECT COUNT(*) FROM sessions 
                WHERE verified = 1 AND (photo_ready = 0 OR photo_ready IS NULL)
                AND created_at > ?
            """, (cutoff_time.isoformat(),))
        
        verified_count = cursor.fetchone()[0]
        
        if verified_count > 0:
            conn.close()
            return 'camera'
        
        # Check for unverified session within verification timeout
        verification_timeout = APIConfig.VERIFICATION_TIMEOUT_MINUTES
        verification_cutoff = datetime.now() - timedelta(minutes=verification_timeout)
        
        if tablet_id:
            cursor.execute("""
                SELECT COUNT(*) FROM sessions 
                WHERE verified = 0 AND tablet_id = ? 
                AND created_at > ?
            """, (tablet_id, verification_cutoff.isoformat()))
        else:
            cursor.execute("""
                SELECT COUNT(*) FROM sessions 
                WHERE verified = 0
                AND created_at > ?
            """, (verification_cutoff.isoformat(),))
        
        unverified_count = cursor.fetchone()[0]
        
        conn.close()
        
        if unverified_count > 0:
            return 'verification'
        
        return 'default'


class MySQLSessionManager:
    """MySQL session manager for production hosting"""
    
    def __init__(self, host, database, user, password, port=3306):
        if not MYSQL_AVAILABLE:
            raise ImportError("mysql-connector-python not available")
        
        self.host = host
        self.database = database
        self.user = user
        self.password = password
        self.port = port
        self.init_db()
        print("✅ MySQL database initialized")
    
    def get_connection(self):
        """Get database connection"""
        try:
            connection = mysql.connector.connect(
                host=self.host,
                database=self.database,
                user=self.user,
                password=self.password,
                port=self.port,
                autocommit=True
            )
            return connection
        except Error as e:
            print(f"❌ Database connection error: {e}")
            return None
    
    def init_db(self):
        """Initialize database tables"""
        connection = self.get_connection()
        if not connection:
            raise Exception("Could not connect to MySQL database")
        
        cursor = connection.cursor()
        
        create_table_query = """
        CREATE TABLE IF NOT EXISTS sessions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            session_id VARCHAR(255) UNIQUE NOT NULL,
            phone VARCHAR(20),
            first_name VARCHAR(100),
            email VARCHAR(255),
            verification_code VARCHAR(6),
            verified BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            photo_path VARCHAR(500),
            photo_data LONGTEXT,
            photo_ready BOOLEAN DEFAULT FALSE,
            tablet_id VARCHAR(100),
            location VARCHAR(100)
        )
        """
        
        try:
            cursor.execute(create_table_query)
            connection.commit()
        except Error as e:
            print(f"❌ Error creating tables: {e}")
            raise
        finally:
            cursor.close()
            connection.close()
    
    def cleanup_old_sessions(self):
        """Clean up old sessions"""
        connection = self.get_connection()
        if not connection:
            return
        
        cursor = connection.cursor()
        timeout_minutes = APIConfig.SESSION_TIMEOUT_MINUTES
        
        cleanup_query = f"""
        DELETE FROM sessions 
        WHERE created_at < DATE_SUB(NOW(), INTERVAL {timeout_minutes} MINUTE)
        """
        
        try:
            cursor.execute(cleanup_query)
            deleted_count = cursor.rowcount
            connection.commit()
            if deleted_count > 0:
                print(f"🧹 Cleaned up {deleted_count} old sessions")
        except Error as e:
            print(f"❌ Error cleaning up sessions: {e}")
        finally:
            cursor.close()
            connection.close()
    
    def create_session(self, first_name, phone, email, verification_code, tablet_id=None, location=None):
        """Create a new session"""
        connection = self.get_connection()
        if not connection:
            return None
        
        cursor = connection.cursor()
        session_id = secrets.token_urlsafe(16)
        
        query = """
        INSERT INTO sessions (session_id, phone, first_name, email, verification_code, verified, tablet_id, location)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        try:
            cursor.execute(query, (session_id, phone, first_name, email, verification_code, False, tablet_id, location))
            connection.commit()
            return session_id
        except Error as e:
            print(f"❌ Error creating session: {e}")
            return None
        finally:
            cursor.close()
            connection.close()
    
    def get_session_by_id(self, session_id):
        """Get session by ID"""
        connection = self.get_connection()
        if not connection:
            return None
        
        cursor = connection.cursor()
        query = "SELECT * FROM sessions WHERE session_id = %s"
        
        try:
            cursor.execute(query, (session_id,))
            result = cursor.fetchone()
            return result
        except Error as e:
            print(f"❌ Error getting session: {e}")
            return None
        finally:
            cursor.close()
            connection.close()
    
    def verify_session(self, session_id, verification_code):
        """Verify session with code"""
        connection = self.get_connection()
        if not connection:
            return False, None
        
        cursor = connection.cursor()
        
        check_query = "SELECT first_name FROM sessions WHERE session_id = %s AND verification_code = %s"
        cursor.execute(check_query, (session_id, verification_code))
        result = cursor.fetchone()
        
        if result:
            update_query = "UPDATE sessions SET verified = TRUE WHERE session_id = %s"
            cursor.execute(update_query, (session_id,))
            connection.commit()
            cursor.close()
            connection.close()
            return True, result[0]
        else:
            cursor.close()
            connection.close()
            return False, None
    
    def get_verified_session(self, tablet_id=None):
        """Get most recent verified session"""
        connection = self.get_connection()
        if not connection:
            return None
        
        cursor = connection.cursor()
        
        if tablet_id:
            query = """
            SELECT first_name, session_id, created_at FROM sessions 
            WHERE verified = TRUE AND (photo_ready = FALSE OR photo_ready IS NULL) 
            AND tablet_id = %s
            ORDER BY created_at DESC LIMIT 1
            """
            cursor.execute(query, (tablet_id,))
        else:
            query = """
            SELECT first_name, session_id, created_at FROM sessions 
            WHERE verified = TRUE AND (photo_ready = FALSE OR photo_ready IS NULL)
            ORDER BY created_at DESC LIMIT 1
            """
            cursor.execute(query)
        
        try:
            result = cursor.fetchone()
            return result
        except Error as e:
            print(f"❌ Error getting verified session: {e}")
            return None
        finally:
            cursor.close()
            connection.close()
    
    def get_unverified_session(self, tablet_id=None):
        """Get most recent unverified session"""
        connection = self.get_connection()
        if not connection:
            return None
        
        cursor = connection.cursor()
        
        if tablet_id:
            query = """
            SELECT first_name, verification_code, created_at FROM sessions 
            WHERE verified = FALSE AND tablet_id = %s
            ORDER BY created_at DESC LIMIT 1
            """
            cursor.execute(query, (tablet_id,))
        else:
            query = """
            SELECT first_name, verification_code, created_at FROM sessions 
            WHERE verified = FALSE
            ORDER BY created_at DESC LIMIT 1
            """
            cursor.execute(query)
        
        try:
            result = cursor.fetchone()
            return result
        except Error as e:
            print(f"❌ Error getting unverified session: {e}")
            return None
        finally:
            cursor.close()
            connection.close()
    
    def update_photo_data(self, session_id, photo_data_b64):
        """Update session with photo data"""
        connection = self.get_connection()
        if not connection:
            return
        
        cursor = connection.cursor()
        cursor.execute('''
            UPDATE sessions 
            SET photo_data = %s, photo_ready = TRUE 
            WHERE session_id = %s
        ''', (photo_data_b64, session_id))
        connection.commit()
        cursor.close()
        connection.close()
    
    def get_photo_data(self, session_id):
        """Get photo data for a session"""
        connection = self.get_connection()
        if not connection:
            return None
        
        cursor = connection.cursor()
        cursor.execute('SELECT photo_ready, photo_data FROM sessions WHERE session_id = %s', (session_id,))
        result = cursor.fetchone()
        cursor.close()
        connection.close()
        return result
    
    def get_session_data(self, session_id):
        """Get full session data"""
        connection = self.get_connection()
        if not connection:
            return None
        
        cursor = connection.cursor()
        cursor.execute('''
            SELECT phone, first_name, email, photo_data FROM sessions WHERE session_id = %s
        ''', (session_id,))
        result = cursor.fetchone()
        cursor.close()
        connection.close()
        return result
    
    def reset_photo_for_retake(self, session_id):
        """Reset photo for retake"""
        connection = self.get_connection()
        if not connection:
            return
        
        cursor = connection.cursor()
        cursor.execute('''
            UPDATE sessions 
            SET photo_ready = FALSE, photo_data = NULL, photo_path = NULL 
            WHERE session_id = %s
        ''', (session_id,))
        connection.commit()
        cursor.close()
        connection.close()
    
    def delete_session(self, session_id):
        """Delete session"""
        connection = self.get_connection()
        if not connection:
            return
        
        cursor = connection.cursor()
        cursor.execute('DELETE FROM sessions WHERE session_id = %s', (session_id,))
        connection.commit()
        cursor.close()
        connection.close()
    
    def reset_all_sessions(self):
        """Reset all sessions"""
        connection = self.get_connection()
        if not connection:
            return 0
        
        cursor = connection.cursor()
        cursor.execute('DELETE FROM sessions')
        deleted_count = cursor.rowcount
        connection.commit()
        cursor.close()
        connection.close()
        return deleted_count
    
    def get_session_stats(self):
        """Get session statistics"""
        connection = self.get_connection()
        if not connection:
            return 0, 0, 0
        
        cursor = connection.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM sessions')
        total_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM sessions WHERE verified = TRUE')
        verified_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM sessions WHERE verified = FALSE')
        unverified_count = cursor.fetchone()[0]
        
        cursor.close()
        connection.close()
        return total_count, verified_count, unverified_count
    
    def get_recent_sessions(self, limit=10):
        """Get recent sessions"""
        connection = self.get_connection()
        if not connection:
            return []
        
        cursor = connection.cursor()
        cursor.execute('''
            SELECT session_id, first_name, phone, verified, verification_code, created_at, photo_ready, 
                   email, photo_path, photo_data, tablet_id, location
            FROM sessions 
            ORDER BY created_at DESC 
            LIMIT %s
        ''', (limit,))
        results = cursor.fetchall()
        cursor.close()
        connection.close()
        return results
    
    def get_session_state(self, tablet_id=None):
        """Get current session state"""
        connection = self.get_connection()
        if not connection:
            return 'error'
        
        cursor = connection.cursor()
        
        # Check for verified session
        if tablet_id:
            cursor.execute("""
                SELECT COUNT(*) FROM sessions 
                WHERE verified = TRUE AND (photo_ready = FALSE OR photo_ready IS NULL) 
                AND tablet_id = %s AND created_at > DATE_SUB(NOW(), INTERVAL 3 MINUTE)
            """, (tablet_id,))
        else:
            cursor.execute("""
                SELECT COUNT(*) FROM sessions 
                WHERE verified = TRUE AND (photo_ready = FALSE OR photo_ready IS NULL)
                AND created_at > DATE_SUB(NOW(), INTERVAL 3 MINUTE)
            """)
        
        verified_count = cursor.fetchone()[0]
        
        if verified_count > 0:
            cursor.close()
            connection.close()
            return 'camera'
        
        # Check for unverified session
        verification_timeout = APIConfig.VERIFICATION_TIMEOUT_MINUTES
        if tablet_id:
            cursor.execute(f"""
                SELECT COUNT(*) FROM sessions 
                WHERE verified = FALSE AND tablet_id = %s 
                AND created_at > DATE_SUB(NOW(), INTERVAL {verification_timeout} MINUTE)
            """, (tablet_id,))
        else:
            cursor.execute(f"""
                SELECT COUNT(*) FROM sessions 
                WHERE verified = FALSE
                AND created_at > DATE_SUB(NOW(), INTERVAL {verification_timeout} MINUTE)
            """)
        
        unverified_count = cursor.fetchone()[0]
        
        cursor.close()
        connection.close()
        
        if unverified_count > 0:
            return 'verification'
        
        return 'default'


def get_session_manager():
    """Factory function to get appropriate session manager"""
    config = APIConfig()
    db_type = config.detect_database_type()
    
    if db_type == 'mysql':
        if not MYSQL_AVAILABLE:
            print("⚠️ MySQL requested but mysql-connector-python not available, falling back to SQLite")
            return SQLiteSessionManager(config.DB_NAME)
        
        try:
            return MySQLSessionManager(
                host=config.DB_HOST,
                database=config.DB_NAME,
                user=config.DB_USER,
                password=config.DB_PASSWORD,
                port=config.DB_PORT
            )
        except Exception as e:
            print(f"❌ MySQL connection failed: {e}")
            print("🔄 Falling back to SQLite")
            return SQLiteSessionManager('fallback.db')
    else:
        return SQLiteSessionManager(config.DB_NAME)