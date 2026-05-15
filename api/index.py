from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI, APIStatusError
import os
import re

app = Flask(__name__)
CORS(app)

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY", "")
)

# DeepSeek V4 Flash: 中文能力强，响应快，免费
MODEL = "deepseek/deepseek-v4-flash:free"

SYSTEM_PROMPT = """你是一个语音识别文字润色工具。

输入：语音识别转出的文字（无标点、口语化、可能有错字）。
输出：一段经过润色的规范书面中文。

你必须遵守以下规则：
1. 直接输出润色后的文字，不要输出任何思考过程、分析步骤、中间结果或解释。
2. 不要用"第一步""第二步"等标记你的处理过程。
3. 不要输出任何markdown标记、代码块、标签。

润色规则（默默执行，不要说出来）：
- 添加正确的标点符号（。！？，、）
- 按语义合理分段
- 删除语气词（嗯、啊、那个、然后等）
- 修正错别字和语病
- 保持原意不变

示例：
输入：嗯那个我今天去了一个很好吃的餐厅然后我们点了很多菜
输出：我今天去了一个很好吃的餐厅，然后我们点了很多菜。

输入：我觉得这个方案有问题首先成本太高然后时间来不及
输出：我觉得这个方案有问题。首先，成本太高。其次，时间来不及。
"""

@app.route('/')
def index():
    return f"""
    <!DOCTYPE html>
    <html><head><meta charset="UTF-8"><title>Typeless AI</title></head>
    <body style="font-family:sans-serif;max-width:600px;margin:50px auto;padding:20px;">
        <h1>Typeless AI Service</h1>
        <p>Model: {MODEL}</p>
        <p>POST /api/polish</p>
    </body></html>
    """, 200, {'Content-Type': 'text/html; charset=utf-8'}

@app.route('/api/polish', methods=['POST', 'OPTIONS'])
def polish_text():
    if request.method == 'OPTIONS':
        return '', 200
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON'}), 400
        user_text = data.get('text', '')
        if not user_text:
            return jsonify({'error': 'Missing text field'}), 400
        if not client.api_key:
            return jsonify({'error': 'API key not configured'}), 500
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_text}
            ],
            temperature=0.1,
            max_tokens=2000
        )
        result = response.choices[0].message.content or ""
        result = result.strip()
        # 去掉markdown代码块
        if result.startswith("```"):
            lines = result.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            result = "\n".join(lines).strip()
        # 去掉思考过程：如果包含"输入：...输出：..."之前有大段分析文字，截取"输出："之后
        if "输出：" in result:
            idx = result.rfind("输出：")
            result = result[idx + 3:].strip()
        # 去重：如果同一段文字连续出现两次，只保留一段
        lines = result.split("\n")
        deduped = []
        for line in lines:
            stripped = line.strip()
            if stripped and deduped and deduped[-1].strip() == stripped:
                continue
            deduped.append(line)
        result = "\n".join(deduped).strip()
        return jsonify({'polished_text': result})
    except APIStatusError as e:
        if e.status_code == 402:
            return jsonify({'error': 'API 额度已用尽 (402 USD spend limit exceeded)，请在 OpenRouter 充值或等待额度重置'}), 402
        return jsonify({'error': f'API 错误: {str(e)}'}), e.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

app_name = app