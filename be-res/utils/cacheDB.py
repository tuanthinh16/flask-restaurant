import sqlite3, time

DB_PATH = 'translation_cache.db'
CACHE_TTL = 3600 * 24  # 1 ngày

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS translation_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_text TEXT,
            source_lang TEXT,
            target_lang TEXT,
            translated_text TEXT,
            created_at INTEGER
        )''')
    clean_expired_cache()

def clean_expired_cache():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('DELETE FROM translation_cache WHERE ? - created_at > ?', (int(time.time()), CACHE_TTL))

def get_cached_translation(text, source, target):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute('''SELECT translated_text, created_at FROM translation_cache
                       WHERE source_text=? AND source_lang=? AND target_lang=?''',
                    (text, source, target))
        row = cur.fetchone()
        if row and time.time() - row[1] < CACHE_TTL:
            return row[0]
        return None

def cache_translation(text, source, target, translated):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        # Kiểm tra xem đã có bản ghi chưa
        cursor.execute('''SELECT 1 FROM translation_cache
                          WHERE source_text = ? AND source_lang = ? AND target_lang = ?''',
                       (text, source, target))
        exists = cursor.fetchone()
        
        if exists:
            # Đã có → update
            cursor.execute('''UPDATE translation_cache
                              SET translated_text = ?, created_at = ?
                              WHERE source_text = ? AND source_lang = ? AND target_lang = ?''',
                           (translated, int(time.time()), text, source, target))
        else:
            # Chưa có → insert
            cursor.execute('''INSERT INTO translation_cache
                              (source_text, source_lang, target_lang, translated_text, created_at)
                              VALUES (?, ?, ?, ?, ?)''',
                           (text, source, target, translated, int(time.time())))
def reset_database():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute('DELETE FROM translation_cache')
        return cursor.rowcount 
