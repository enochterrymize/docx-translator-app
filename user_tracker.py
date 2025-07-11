import hashlib
import json
import os
import sqlite3
import uuid
from datetime import date, datetime

import streamlit as st


class UserTracker:
    def __init__(self, db_path="users.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """Initialize the database with required tables."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Daily usage tracking
        c.execute(
            """CREATE TABLE IF NOT EXISTS daily_usage
                     (user_id TEXT, 
                      date TEXT,
                      translation_count INTEGER DEFAULT 0,
                      last_used TIMESTAMP,
                      PRIMARY KEY (user_id, date))"""
        )

        # User sessions
        c.execute(
            """CREATE TABLE IF NOT EXISTS user_sessions
                     (user_id TEXT,
                      session_id TEXT,
                      created_at TIMESTAMP,
                      last_activity TIMESTAMP,
                      ip_address TEXT,
                      user_agent TEXT)"""
        )

        # Translation history
        c.execute(
            """CREATE TABLE IF NOT EXISTS translations
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      user_id TEXT,
                      file_name TEXT,
                      src_lang TEXT,
                      dest_lang TEXT,
                      translation_method TEXT,
                      created_at TIMESTAMP)"""
        )

        conn.commit()
        conn.close()

    def get_user_id(self):
        """Get or create a user ID using multiple methods."""
        # Try to get from session state first
        if "user_id" in st.session_state:
            return st.session_state.user_id

        # Try to get from query parameters (cookie-like)
        query_params = st.experimental_get_query_params()
        if "user_id" in query_params:
            user_id = query_params["user_id"][0]
            st.session_state.user_id = user_id
            return user_id

        # Create new user ID
        user_id = str(uuid.uuid4())
        st.session_state.user_id = user_id

        # Set in query parameters for persistence
        st.experimental_set_query_params(user_id=user_id)

        return user_id

    def get_daily_count(self, user_id):
        """Get the number of translations for a user today."""
        today = str(date.today())
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            """SELECT translation_count FROM daily_usage 
                     WHERE user_id = ? AND date = ?""",
            (user_id, today),
        )
        result = c.fetchone()
        conn.close()
        return result[0] if result else 0

    def increment_count(self, user_id, file_name, src_lang, dest_lang, method):
        """Increment the daily count and log the translation."""
        today = str(date.today())
        now = datetime.now()

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Update daily usage
        c.execute(
            """INSERT OR REPLACE INTO daily_usage 
                     VALUES (?, ?, COALESCE(
                         (SELECT translation_count FROM daily_usage 
                          WHERE user_id = ? AND date = ?), 0) + 1, ?)""",
            (user_id, today, user_id, today, now),
        )

        # Log translation
        c.execute(
            """INSERT INTO translations 
                     (user_id, file_name, src_lang, dest_lang, translation_method, created_at)
                     VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, file_name, src_lang, dest_lang, method, now),
        )

        conn.commit()
        conn.close()

    def can_translate(self, user_id, daily_limit=5):
        """Check if user can translate (within daily limit)."""
        current_count = self.get_daily_count(user_id)
        return current_count < daily_limit

    def get_user_stats(self, user_id):
        """Get comprehensive user statistics."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Total translations
        c.execute("SELECT COUNT(*) FROM translations WHERE user_id = ?", (user_id,))
        total_translations = c.fetchone()[0]

        # Today's count
        today_count = self.get_daily_count(user_id)

        # Most used languages
        c.execute(
            """SELECT src_lang, dest_lang, COUNT(*) as count 
                     FROM translations 
                     WHERE user_id = ? 
                     GROUP BY src_lang, dest_lang 
                     ORDER BY count DESC 
                     LIMIT 5""",
            (user_id,),
        )
        popular_languages = c.fetchall()

        # First translation date
        c.execute(
            """SELECT MIN(created_at) FROM translations WHERE user_id = ?""", (user_id,)
        )
        first_translation = c.fetchone()[0]

        conn.close()

        return {
            "total_translations": total_translations,
            "today_count": today_count,
            "popular_languages": popular_languages,
            "first_translation": first_translation,
        }

    def get_analytics(self):
        """Get overall app analytics (for admin)."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Total users
        c.execute("SELECT COUNT(DISTINCT user_id) FROM translations")
        total_users = c.fetchone()[0]

        # Total translations
        c.execute("SELECT COUNT(*) FROM translations")
        total_translations = c.fetchone()[0]

        # Today's activity
        today = str(date.today())
        c.execute(
            "SELECT COUNT(DISTINCT user_id) FROM daily_usage WHERE date = ?", (today,)
        )
        active_today = c.fetchone()[0]

        # Popular language pairs
        c.execute(
            """SELECT src_lang, dest_lang, COUNT(*) as count 
                     FROM translations 
                     GROUP BY src_lang, dest_lang 
                     ORDER BY count DESC 
                     LIMIT 10"""
        )
        popular_pairs = c.fetchall()

        conn.close()

        return {
            "total_users": total_users,
            "total_translations": total_translations,
            "active_today": active_today,
            "popular_pairs": popular_pairs,
        }


# Global tracker instance
tracker = UserTracker()
