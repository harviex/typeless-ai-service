from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
import os

app = Flask(__name__)
CORS(app)

# OpenRouter client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY", "")
)

# System prompt for text polishing
SYSTEM_PROMPT = """你是一个专业的文本润色助手。请对用户输入的文字进行以下处理：

1. **去除口语化用词**：删除"嗯、啊、那个、然后"等口头禅，转为书面语。
2. **删除冗余逻辑**：去除重复语句、自相矛盾或逻辑混乱的内容，保证文字通顺。
3. **结构化排版**：
   - 将长文分段，每段不超过3-4行。
   - 使用**序号标签**（一、二、三...）或**分级序号**（1.1, 1.2, 2.1...）。
   - 如果是清单/建议，使用Markdown列表（- 或 1.）。
4. **保持原意**：润色后必须保留原文本的核心信息和意图。

直接返回润色后的文字，不要添加任何解释或开场白。
"""

@app.route('/')
def index():
    # 返回极简HTML，避免超时
    return """
    <!DOCTYPE html>
    <html><head><meta charset="UTF-8"><title>Typeless AI</title></head>
    <body style="font-family:sans-serif;max-width:600px;margin:50px auto;padding:20px;">
        <h1>✨ Typeless AI Service</h1>
        <p>文本润色API | POST /api/polish</p>
        <hr>
        <h3>测试</h3>
        <form onsubmit="testAPI(); return false;">
            <textarea id="input" style="width:100%;height:80px;" placeholder="输入文字..."></textarea><br>
            <button type="submit">润色</button>
        </form>
        <pre id="output" style="background:#f5f5f5;padding:10px;margin-top:10px;"></pre>
        <script>
        async function testAPI() {
            const text = document.getElementById('input').value;
            const res = await fetch('/api/polish', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({text})
            });
            const data = await res.json();
            document.getElementById('output').innerText = data.polished_text || data.error;
        }
        </script>
    </body></html>
    """, 200, {'Content-Type': 'text/html; charset=utf-8'}

@app.route('/api/polish', methods=['POST', 'OPTIONS'])
def polish_text():
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        # Parse request
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON'}), 400
            
        user_text = data.get('text', '')
        
        if not user_text:
            return jsonify({'error': 'Missing text field'}), 400
        
        # Validate API key
        if not client.api_key:
            return jsonify({'error': 'OPENROUTER_API_KEY not configured'}), 500
        
        # Call OpenRouter API - 使用指定的免费模型
        response = client.chat.completions.create(
            model="nvidia/nemotron-3-super-120b-a12b:free",  # 用户指定模型
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_text}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        polished_text = response.choices[0].message.content
        return jsonify({'polished_text': polished_text})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# For Vercel serverless deployment
app_name = app
