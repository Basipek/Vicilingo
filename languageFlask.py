import os
import json
import requests
from flask import Blueprint, render_template, jsonify, request
import eventlet
eventlet.monkey_patch()

from dotenv import load_dotenv

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
    user_data = request.json
    ingredients = user_data.get('ingredients', [])

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
    You are the Vicilingo Game Engine. Your task is to generate language-learning exercises.

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
          "topic": "Topic Name",
          "question": "Example question text with Furigana (読み方) for Kanji?",
          "options": ["A", "B", "C", "D"],
          "answer": "A"
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
    
    print(prompt)
    print("\n////PROMPT SENT TO OPENROUTER////")

    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions", 
            headers=headers, 
            data=json.dumps(payload)
        )
        ai_res = response.json()
        
        print(ai_res)
        print("\n////OPENROUTER RESPONSE////")
        
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
