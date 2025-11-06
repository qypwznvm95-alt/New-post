# database.py
import sqlite3
import logging
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Инициализация всех таблиц базы данных"""
        tables = [
            # Таблица пользователей
            '''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                phone TEXT,
                region TEXT,
                interest_level INTEGER DEFAULT 0,
                last_contact TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''',
            
            # Таблица сообщений
            '''
            CREATE TABLE IF NOT EXISTS user_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                message_text TEXT,
                message_type TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
            ''',
            
            # Таблица интересов
            '''
            CREATE TABLE IF NOT EXISTS user_interests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                interest_type TEXT,
                interest_details TEXT,
                interest_level INTEGER DEFAULT 1,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
            ''',
            
            # Таблица отправленных предложений
            '''
            CREATE TABLE IF NOT EXISTS sent_offers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                offer_type TEXT,
                offer_file_path TEXT,
                sent_status TEXT DEFAULT 'sent',
                opened_at TIMESTAMP NULL,
                response_received BOOLEAN DEFAULT FALSE,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
            ''',
            
            # Таблица регионов
            '''
            CREATE TABLE IF NOT EXISTS regions (
                region_name TEXT PRIMARY KEY,
                telegram_channels TEXT,
                chat_groups TEXT,
                potential_clients INTEGER,
                analysis_data TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            '''
        ]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for table_sql in tables:
            cursor.execute(table_sql)
        
        conn.commit()
        conn.close()
    
    def add_user(self, user_id: int, username: str, first_name: str, last_name: str = ""):
        """Добавление нового пользователя"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO users (user_id, username, first_name, last_name, last_contact)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (user_id, username, first_name, last_name))
        
        conn.commit()
        conn.close()
    
    def log_message(self, user_id: int, message_text: str, message_type: str = "text"):
        """Логирование сообщения пользователя"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO user_messages (user_id, message_text, message_type)
            VALUES (?, ?, ?)
        ''', (user_id, message_text, message_type))
        
        conn.commit()
        conn.close()
    
    def log_interest(self, user_id: int, interest_type: str, details: str = ""):
        """Логирование интереса пользователя"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO user_interests (user_id, interest_type, interest_details)
            VALUES (?, ?, ?)
        ''', (user_id, interest_type, details))
        
        conn.commit()
        conn.close()
    
    def log_offer_sent(self, user_id: int, offer_type: str, file_path: str = ""):
        """Логирование отправки предложения"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO sent_offers (user_id, offer_type, offer_file_path)
            VALUES (?, ?, ?)
        ''', (user_id, offer_type, file_path))
        
        conn.commit()
        conn.close()
    
    def has_received_offer(self, user_id: int) -> bool:
        """Проверка, получал ли пользователь предложение"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT 1 FROM sent_offers WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        conn.close()
        
        return result is not None
    
    def update_user_region(self, user_id: int, region: str):
        """Обновление региона пользователя"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users SET region = ?, last_contact = CURRENT_TIMESTAMP 
            WHERE user_id = ?
        ''', (region, user_id))
        
        conn.commit()
        conn.close()
    
    def get_user_messages(self, user_id: int) -> List[Dict]:
        """Получение истории сообщений пользователя"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT message_text, message_type, timestamp 
            FROM user_messages 
            WHERE user_id = ? 
            ORDER BY timestamp
        ''', (user_id,))
        
        messages = []
        for row in cursor.fetchall():
            messages.append({
                'text': row[0],
                'type': row[1],
                'timestamp': row[2]
            })
        
        conn.close()
        return messages
    
    def get_user_interests(self, user_id: int) -> List[Dict]:
        """Получение интересов пользователя"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT interest_type, interest_details, timestamp 
            FROM user_interests 
            WHERE user_id = ? 
            ORDER BY timestamp
        ''', (user_id,))
        
        interests = []
        for row in cursor.fetchall():
            interests.append({
                'type': row[0],
                'details': row[1],
                'timestamp': row[2]
            })
        
        conn.close()
        return interests
