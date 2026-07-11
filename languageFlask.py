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

@language_bp.route('/api/nodes/<filename>')
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
    topics = user_data.get('topics', ['General'])
    difficulty = user_data.get('difficulty', 'A1')

    prompt = f"""
    Generate a JSON object containing a language learning exercise for topics: {', '.join(topics)}.
    Difficulty: {difficulty}. 
    Return strictly JSON matching this structure:
    {{
      "question": "The question string",
      "options": ["choice A", "choice B", "choice C"],
      "answer": "The correct choice matching exactly"
    }}
    Do not return markdown formatting blocks, just the raw JSON text.
    """

    # Mirroring OpenRouter's exact documentation header setup
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://antixbasipek.taile1bff7.ts.net/language", # Optional but recommended by docs
        "X-OpenRouter-Title": "Vicilingo"
    }
    
    # Exact payload structure match
    payload = {
        "model": "poolside/laguna-m.1:free", 
        "messages": [{"role": "user", "content": prompt}]
    }

    try:
        # Using exact documented style: data=json.dumps(payload)
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions", 
            headers=headers, 
            data=json.dumps(payload)
        )
        ai_res = response.json()
        
        # Guardrail check for payload structural issues
        if 'choices' not in ai_res:
            return jsonify({"error": "OpenRouter API error", "details": ai_res}), 500
            
        ai_text = ai_res['choices'][0]['message']['content'].strip()
        
        # Clean up code fences if the model wraps its output in markdown block wrappers anyway
        if ai_text.startswith("```json"):
            ai_text = ai_text.split("```json")[1].split("```")[0].strip()
        elif ai_text.startswith("```"):
            ai_text = ai_text.split("```")[1].split("```")[0].strip()

        return jsonify(json.loads(ai_text))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

#if __name__ == '__main__':
    #app.run(port=5001, debug=True)
