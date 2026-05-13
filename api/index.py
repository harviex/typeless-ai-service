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

# System prompt - 语音输入智能润色模式
SYSTEM_PROMPT = """你是一个专业的中文语音输入润色工具。用户对文字说话（语音识别转文字），请进行以下处理：

【标点符号】
- 自动添加正确的标点符号（句号、逗号、问号、感叹号等）
- 疑问语气（吗、呢、什么、怎么、哪里、为什么等）使用问号
- 感叹语气使用感叹号
- 一般陈述句使用句号
- 长句中间添加逗号分隔

【分段与结构】
- 按语义和话题合理分段，每段不超过3-4行
- 不同话题/要点之间必须分段
- 如果是多个并列要点，使用分点格式：一、二、三 或 1. 2. 3.
- 如果是步骤/流程，使用序号：第一步、第二步 或 1. 2. 3.
- 如果是建议/清单，使用短横线列表：- xxx

【文字润色】
- 去除口语化用词：嗯、啊、那个、然后、就是、的话、呃、哦、呢（句末语气词除外）
- 删除重复、冗余、自相矛盾的句子
- 修正明显的语病和错别字
- 保持原文的核心信息、意图和语气

【输出要求】
- 直接返回润色后的原文，不要任何开场白或解释
- 如果原文已经很规范，返回原文即可
- 不要添加原文中没有的新信息、建议或观点
- 不要改变原文的观点和立场

示例1（口语转书面）：
输入："嗯，那个，我今天去了公园，然后，就是看到了很多花，然后很开心"
输出："我今天去了公园，看到了很多花，很开心。"

示例2（自动标点+分段）：
输入："首先我们要注意安全问题然后是关于预算的问题我觉得应该增加十万还有人员的安排需要调整一下"
输出：
"首先，我们要注意安全问题。

其次，关于预算的问题，我觉得应该增加十万。

最后，人员的安排需要调整一下。"

示例3（疑问句自动加问号）：
输入："你觉得这个方案怎么样我们是不是应该再讨论一下"
输出："你觉得这个方案怎么样？我们是不是应该再讨论一下？"
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
