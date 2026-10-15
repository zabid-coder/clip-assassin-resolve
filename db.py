import sqlite3
import os
import platform

def get_app_data_dir():
    app_name = "ClipAssassin"
    if platform.system() == "Windows":
        base = os.environ.get('APPDATA', os.path.expanduser('~'))
        return os.path.join(base, app_name)
    elif platform.system() == "Darwin":
        return os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', app_name)
    else:
        return os.path.join(os.path.expanduser('~'), f".{app_name.lower()}")

data_dir = os.path.dirname(os.path.abspath(os.environ["CLIP_ASSASSIN_DB_PATH"])) if os.environ.get("CLIP_ASSASSIN_DB_PATH") else get_app_data_dir()
if not os.path.exists(data_dir):
    os.makedirs(data_dir)

DB_PATH = os.environ.get("CLIP_ASSASSIN_DB_PATH", os.path.join(data_dir, "settings.db"))

def get_db_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS export_presets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            data TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_setting(key, default=""):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT value FROM settings WHERE key = ?', (key,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else default

def set_setting(key, value):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', (key, value))
    conn.commit()
    conn.close()

def get_all_settings():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT key, value FROM settings')
    rows = c.fetchall()
    conn.close()
    return {row[0]: row[1] for row in rows}

def get_all_presets():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT id, name, data FROM export_presets')
    rows = c.fetchall()
    conn.close()
    import json
    return [{"id": row[0], "name": row[1], "data": json.loads(row[2])} for row in rows]

def save_preset(name, data_dict):
    import json
    data_str = json.dumps(data_dict)
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO export_presets (name, data) VALUES (?, ?)', (name, data_str))
    conn.commit()
    conn.close()

def delete_preset(preset_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('DELETE FROM export_presets WHERE id = ?', (preset_id,))
    conn.commit()
    conn.close()

# Initialize database on module load
init_db()


# Folder templates use the validated IngestTemplate schema, separate from render presets.
def save_folder_template(template):
    with get_db_connection() as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS folder_templates (id TEXT PRIMARY KEY, data TEXT NOT NULL)")
        conn.execute("INSERT OR REPLACE INTO folder_templates VALUES (?, ?)", (template.id, template.to_json()))


def get_folder_templates():
    import json
    with get_db_connection() as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS folder_templates (id TEXT PRIMARY KEY, data TEXT NOT NULL)")
        return [json.loads(row[0]) for row in conn.execute("SELECT data FROM folder_templates ORDER BY id")]


def delete_folder_template(template_id):
    with get_db_connection() as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS folder_templates (id TEXT PRIMARY KEY, data TEXT NOT NULL)")
        return conn.execute("DELETE FROM folder_templates WHERE id = ?", (template_id,)).rowcount > 0
