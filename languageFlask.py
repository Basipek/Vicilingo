import os
import json
import requests
from flask import Blueprint, render_template, jsonify, request
import eventlet
eventlet.monkey_patch()

from dotenv import load_dotenv

import sys
from pathlib import Path

import sqlite3

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vicilingo_users.db")

def init_db():
    """Initializes and automatically updates the Vicilingo user XP tracking tables."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # 1. Create the base table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_xp (
            nickname TEXT NOT NULL,
            language TEXT NOT NULL,
            topic TEXT NOT NULL,
            xp INTEGER DEFAULT 0,
            PRIMARY KEY (nickname, topic)
        )
    ''')
    
    # 2. Define your desired schema (including any new columns you add in the future)
    # format: "column_name": "DATA_TYPE CONTRAINTS"
    target_columns = {
        "nickname": "TEXT NOT NULL",
        "language": "TEXT NOT NULL",
        "topic": "TEXT NOT NULL",
        "xp": "INTEGER DEFAULT 0",
        # --- ADD YOUR FUTURE COLUMNS HERE ---
        # "streak": "INTEGER DEFAULT 0",
        # "last_active": "TEXT",
    }
    
    # 3. Get currently existing columns in the database
    cursor.execute("PRAGMA table_info(user_xp)")
    existing_columns = {row[1] for row in cursor.fetchall()}  # row[1] is the column name
    
    # 4. Compare and add missing columns
    for col_name, col_def in target_columns.items():
        if col_name not in existing_columns:
            # Safely append the new column
            cursor.execute(f"ALTER TABLE user_xp ADD COLUMN {col_name} {col_def}")
            print(f"Added missing column: {col_name}")

    conn.commit()
    conn.close()

# Auto-initialize on module load
init_db()

# Expand the home directory (~) and add the specific directory to sys.path
sicrit_path = Path.home() / "scripts_py" / "webinterfacesip"
sys.path.append(str(sicrit_path))

# Now you can safely import the functions
from sicrit import session_is_auth2, session_is_auth

# Load the keys out of your hidden .env file
load_dotenv()

# Note the static_url_path change so its assets don't collide with the main app
language_bp = Blueprint('vicilingo', __name__, 
                        static_folder='static', 
                        template_folder='templates',
                        static_url_path='/language/static')

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "MISSING_ENV_KEY")

@language_bp.route('/')
def index():
    # Renders the HTML canvas layout
    return render_template('indexLanguage.html')

@language_bp.route('/api/nodes/all')
def get_all_nodes():
    """
    Dynamically scans the languagegame directory, reads all .json files,
    and aggregates them into a single cohesive structural payload.
    """
    target_dir = os.path.join(language_bp.static_folder, 'languagegame')
    combined_data = {
        "languages": {}
    }
    
    try:
        if not os.path.exists(target_dir):
            return jsonify({"error": f"Directory structural path missing: {target_dir}"}), 404
            
        # Scan everything inside the folder
        for filename in os.listdir(target_dir):
            if filename.endswith('.json'):
                file_path = os.path.join(target_dir, filename)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        file_json = json.load(f)
                        
                    lang_name = file_json.get('language', 'Unknown')
                    section_name = file_json.get('section', filename.replace('.json', ''))
                    file_nodes = file_json.get('nodes', [])
                    
                    # Initialize language tracking matrix if missing
                    if lang_name not in combined_data["languages"]:
                        combined_data["languages"][lang_name] = {}
                        
                    # Append node matrices grouped cleanly by sections
                    combined_data["languages"][lang_name][section_name] = file_nodes
                    
                except (json.JSONDecodeError, IOError) as e:
                    # Skip or log corrupted files silently so one broken file won't crash the whole map load
                    print(f" [!] Error reading structural file {filename}: {str(e)}")
                    continue

        return jsonify(combined_data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@language_bp.route('/api/nodesfrom/<filename>')
def get_nodes(filename):
    # Dynamically loads node files systems
    try:
        file_path = os.path.join(language_bp.static_folder, 'languagegame', f"{filename}.json")
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify(data)
    except FileNotFoundError:
        return jsonify({"error": "Node map file not found"}), 404

@language_bp.route('/api/generate-exercise', methods=['POST'])
def generate_exercise():
    data = request.get_json() or {}
    
    # Extract credentials
    nickname = data.get('nickname') or 'Anonymous'
    session_key = data.get('session_key')
    
    # Enforce Auth Lock
    if not session_is_auth(nickname, session_key):
        return jsonify({"status": "error", "message": "Not logged in."}), 403

    # Existing logic continues below...
    ingredients = data.get('ingredients', [])

    if not ingredients:
        return jsonify({"error": "No exercise components supplied to gym recipe matrix"}), 400

    # Build an isolated text block detailing each topic item's structural properties
    recipe_blocks = []
    for index, ing in enumerate(ingredients, 1):
        block = f"""  Ingredient #{index}:
  - Language: {ing.get('language', 'Unknown')}
  - Topic Target: {ing.get('topic', 'General')}
  - Target Difficulty: {ing.get('difficulty', 'A1')}
  - Context Description: {ing.get('description', 'No context')}
  - Accompanying Cheatsheet: {ing.get('cheatsheet', 'None')}"""
        recipe_blocks.append(block)

    structured_ingredients_str = "\n\n".join(recipe_blocks)

    prompt = f"""
    You are the Vicilingo Game Engine. Your task is to generate topic-learning exercises.

    ### INPUT DATA:
    {structured_ingredients_str}

    ### RULES:
    1. QUANTITY: For EACH ingredient topic above, generate exactly 5 unique questions.
    2. DIFFICULTY SCALING: 
       - Align questions with the "Target Difficulty". 
       - A1: Native script only (No Kanji). 
       - A2-B2: Include Kanji + Furigana (Hiragana readings).
       - C1+: Full native script without mandatory Furigana.
    3. FORMAT: Return JSON only. No markdown (```json), no conversational filler.
    4. VALIDATION: Ensure the 'answer' field matches one of the strings in the 'options' array EXACTLY.

    ### JSON STRUCTURE EXAMPLE:
    {{
      "exercises": [
        {{
          "topic": "Topic Name as given",
          "language": "Language as given",
          "question": "Example question text with Furigana (読み方) for Kanji?",
          "options": ["A", "B", "C", "D"],
          "answer": "EXACT STRING MATCHING THE ANSWER"
        }}
      ]
    }}

    ### CURRENT EXERCISES:
    """

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://antixbasipek.taile1bff7.ts.net/language",
        "X-OpenRouter-Title": "Vicilingo"
    }
    #nvidia/nemotron-3.5-content-safety:free
    #poolside/laguna-m.1:free
    payload = {
        "model": "poolside/laguna-m.1:free", 
        "messages": [{"role": "user", "content": prompt}]
    }
    
    #print(prompt)
    print("\n////PROMPT SENT TO OPENROUTER////")
    print(f"\n////PROMPT SENT BY {nickname}////O0+--")

    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions", 
            headers=headers, 
            data=json.dumps(payload)
        )
        ai_res = response.json()
        
        #print(ai_res)
        print("\n////OPENROUTER RESPONSE////")
        print(f"////RESPONSE FOR {nickname}////O0+--")
        
        if 'choices' not in ai_res:
            return jsonify({"error": "OpenRouter API error", "details": ai_res}), 500
            
        ai_text = ai_res['choices'][0]['message']['content'].strip()
        
        # Robust trimming of any markdown code blocks if the LLM slips up
        if ai_text.startswith("```json"):
            ai_text = ai_text.split("```json")[1].split("```")[0].strip()
        elif ai_text.startswith("```"):
            ai_text = ai_text.split("```")[1].split("```")[0].strip()

        return jsonify(json.loads(ai_text))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

#if __name__ == '__main__':
    #app.run(port=5001, debug=True)

@language_bp.route('/api/user/get-xp', methods=['POST'])
def get_xp():
    """Retrieves the complete XP progress table for an authenticated user."""
    data = request.get_json() or {}
    nickname = data.get('nickname') or 'Anonymous'
    session_key = data.get('session_key')
    
    if not session_is_auth(nickname, session_key):
        return jsonify({"status": "error", "message": "Not logged in."}), 403
        
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT topic, xp, language FROM user_xp WHERE nickname = ?", (nickname,))
        rows = cursor.fetchall()
        conn.close()
        
        topics_list = [{"topic": row["topic"], "xp": row["xp"], "language": row["language"]} for row in rows]
        return jsonify({"status": "success", "topics": topics_list})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@language_bp.route('/api/user/update-xp', methods=['POST'])
def update_xp():
    """Updates/Increments the user's progress for a specific node topic."""
    data = request.get_json() or {}
    nickname = data.get('nickname') or 'Anonymous'
    session_key = data.get('session_key')
    topic = data.get('topic')
    language = data.get('language')
    change = data.get('change', 0)
    
    if not session_is_auth(nickname, session_key):
        return jsonify({"status": "error", "message": "Not logged in."}), 403
        
    if not topic:
        return jsonify({"status": "error", "message": "No topic supplied."}), 400
        
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute("SELECT xp FROM user_xp WHERE nickname = ? AND topic = ? AND language = ?", (nickname, topic, language))
        row = cursor.fetchone()
        
        if row is None:
            new_xp = max(0, min(100, change))
            cursor.execute("INSERT INTO user_xp (nickname, language, topic, xp) VALUES (?, ?, ?, ?)", (nickname, language, topic, new_xp))
        else:
            new_xp = max(0, min(100, row[0] + change))
            cursor.execute("UPDATE user_xp SET xp = ? WHERE nickname = ? AND topic = ? AND language = ?", (new_xp, nickname, topic, language))
            
        conn.commit()
        conn.close()
        
        return jsonify({"status": "success","language": language, "topic": topic, "xp": new_xp})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@language_bp.route('/api/user/forget-topic', methods=['POST'])
def forget_topic():
    """Resets or deletes tracking progress of a given topic node."""
    data = request.get_json() or {}
    nickname = data.get('nickname') or 'Anonymous'
    session_key = data.get('session_key')
    topic = data.get('topic')
    language = data.get('language')
    
    if not session_is_auth(nickname, session_key):
        return jsonify({"status": "error", "message": "Not logged in."}), 403
        
    if not topic:
        return jsonify({"status": "error", "message": "No topic supplied."}), 400
        
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM user_xp WHERE nickname = ? AND topic = ? AND language = ?", (nickname, topic, language))
        conn.commit()
        conn.close()
        
        return jsonify({"status": "success", "message": f"Forgot topic: {topic} from {language}"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500