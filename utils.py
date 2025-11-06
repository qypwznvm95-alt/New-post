import sqlite3
from datetime import datetime, timedelta

class Analytics:
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def get_regional_stats(self):
        """Статистика по регионам"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT region, COUNT(*) as user_count 
            FROM users 
            WHERE region IS NOT NULL 
            GROUP BY region 
            ORDER BY user_count DESC
        ''')
        
        return cursor.fetchall()
    
    def get_offer_stats(self):
        """Статистика отправленных предложений"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT DATE(sent_at), COUNT(*) 
            FROM sent_offers 
            GROUP BY DATE(sent_at) 
            ORDER BY DATE(sent_at) DESC 
            LIMIT 7
        ''')
        
        return cursor.fetchall()

class RegionManager:
    """Управление регионами и анализом"""
    
    def __init__(self):
        self.analyzed_regions = {}
    
    def add_region_analysis(self, region: str, analysis: Dict):
        """Добавление анализа региона в базу"""
        conn = sqlite3.connect("car_sales_bot.db")
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO regions 
            (region_name, telegram_channels, chat_groups, potential_clients, analysis_data)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            region,
            str(analysis['telegram_channels']),
            str(analysis['chat_groups']),
            analysis['estimated_clients'],
            str(analysis)
        ))
        
        conn.commit()
        conn.close()
