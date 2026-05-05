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

# System prompt - 严格润色模式
SYSTEM_PROMPT = """你是一个文本格式化和润色工具。严格遵循以下规则：

【必须做】
1. 去除口语化用词：嗯、啊、那个、然后、就是、的话、呃...
2. 删除冗余重复的句子
3. 修正明显的语病和错别字
4. 合理分段（每段3-4行）
5. 保持原文的所有信息和意图

【绝对禁止】
❌ 不回答用户的问题
❌ 不添加任何新信息、建议、解释
❌ 不写"以下是润色后的文字"等开场白
❌ 不改变原文的观点、语气、风格
❌ 不提供解决方案或建议

【输出要求】
- 直接返回润色后的原文
- 如果原文已经很好，返回原文即可
- 只做最小必要的修改

示例：
输入："嗯，那个，我今天去了公园，然后，就是看到了很多花，然后很开心"
输出："我今天去了公园，看到了很多花，很开心。"
"""

@app.route('/')
def index():
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
        
        # Call OpenRouter API
        response = client.chat.completions.create(
            model="nvidia/nemotron-3-super-120b-a12b:free",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_text}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        
        polished_text = response.choices[0].message.content
        return jsonify({'polished_text': polished_text})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# For Vercel serverless deployment
app_name = app
