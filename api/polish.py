from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
import os

app = Flask(__name__)
CORS(app)

# OpenRouter client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY", "YOUR_OPENROUTER_API_KEY_HERE")
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
    return """
    <html>
    <head><title>Typeless AI Service</title></head>
    <body style="font-family: sans-serif; max-width: 600px; margin: 50px auto; padding: 20px;">
        <h1>✨ Typeless AI Service</h1>
        <p>文本润色API服务，基于OpenRouter免费模型。</p>
        <h2>使用方法</h2>
        <pre>curl -X POST https://你的域名.vercel.app/api/polish \\
  -H "Content-Type: application/json" \\
  -d '{"text": "嗯，那个，我想去吃饭"}'</pre>
        <h2>功能</h2>
        <ul>
            <li>去除口语化用词</li>
            <li>删除冗余逻辑</li>
            <li>结构化排版</li>
            <li>保持原意</li>
        </ul>
    </body>
    </html>
    """

@app.route('/api/polish', methods=['POST', 'OPTIONS'])
def polish_text():
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        # Parse request
        data = request.get_json()
        user_text = data.get('text', '')
        
        if not user_text:
            return jsonify({'error': 'Missing text field'}), 400
        
        # Call OpenRouter API
        response = client.chat.completions.create(
            model="meta-llama/llama-3.3-8b-instruct:free",  # Free model on OpenRouter
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

# Vercel requires the app to be named 'app'
if __name__ == '__main__':
    app.run(debug=True)
