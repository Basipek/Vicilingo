import os
import json
import requests
from flask import Flask, render_template, jsonify, request

app = Flask(__name__, 
            static_folder='static', 
            template_folder='templates')

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "your_fallback_key_here")

@app.route('/')
def index():
    # Renders the HTML canvas layout
    return render_template('index.html')

@app.route('/api/nodes/<filename>')
def get_nodes(filename):
    # Dynamically loads node files systems
    try:
        file_path = os.path.join(app.static_folder, 'languagegame', f"{filename}.json")
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify(data)
    except FileNotFoundError:
        return jsonify({"error": "Node map file not found"}), 404

@app.route('/api/generate-exercise', methods=['POST'])
def generate_exercise():
    # Prompting payload structure for OpenRouter
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
    Do not return markdown formatting blocks, just the raw JSON.
    """

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Using openrouter free tier (e.g., Google Gemma 2 or similar current free variant)
    payload = {
        "model": "google/gemma-2-9b-it:free", 
        "messages": [{"role": "user", "content": prompt}]
    }

    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
        ai_res = response.json()
        ai_text = ai_res['choices'][0]['message']['content'].strip()
        
        # Clean up accidental markdown blocks from LLMs if present
        if ai_text.startswith("```json"):
            ai_text = ai_text.split("```json")[1].split("```")[0].strip()

        return jsonify(json.loads(ai_text))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(port=5001, debug=True)
