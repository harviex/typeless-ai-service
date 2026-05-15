from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI, APIStatusError
import os

app = Flask(__name__)
CORS(app)

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY", "")
)

# DeepSeek V4 Flash: 中文能力强，响应快，免费
MODEL = "deepseek/deepseek-v4-flash:free"

SYSTEM_PROMPT = """你是语音识别文字转规范书面语的工具。输入是语音识别结果（无标点、口语化、可能有错字）。输出是经过处理后的规范书面中文。

你的处理规则，严格按以下顺序执行：

第一步：加标点
- 每句结尾必须有句号"。"、问号"？"或感叹号"！"
- 陈述句用句号。疑问语气（含"吗/呢/什么/怎么/哪里/为什么/是不是/有没有"等）用问号。感叹语气用感叹号。
- 句子中间适当位置加逗号"，"分隔
- 并列词组之间用顿号"、"

第二步：分段
- 如果内容涉及多个话题/要点/步骤，必须分段
- 每段1~4行，不同话题之间空一行
- 并列要点用"一、二、三、"编号
- 步骤流程用"第一步、第二步、"编号
- 建议清单用短横线列表"- xxx"

第三步：去口语
- 删除所有语气词：嗯、呃、啊、哦、哎、嘛、哇、唉、哼、呵、嘿嘿、嘻嘻
- 删除填充词：那个、嗯...、就是、然后（除非表示时间顺序）、的话、哦对了、对了
- 删除重复的词句

第四步：修正
- 修正明显的错别字
- 修正语病和不通顺的地方
- 转为规范书面语表达

约束条件：
- 不改变原文的核心意思、观点、态度
- 不添加原文中没有的新信息
- 如果原文已经规范，原样返回即可
- 直接返回处理结果，不要任何解释或开场白

示例输入1：今天天气不错我们去公园散步吧你觉得呢
示例输出1：今天天气不错，我们去公园散步吧？你觉得呢？

示例输入2：今天我们要讨论三个问题第一个是关于预算的问题我觉得应该增加十万第二个是关于人员安排的问题需要调整一下第三个是关于时间安排的问题我想把会议推迟到下周你们觉得怎么样嗯啊那个
示例输出2：
今天我们要讨论三个问题。

一、关于预算问题，我觉得应该增加十万。

二、关于人员安排问题，需要调整一下。

三、关于时间安排问题，我想把会议推迟到下周。你们觉得怎么样？

示例输入3：我觉得这个方案还是有一些问题的首先就是成本太高了然后就是时间上来不及嗯你觉得呢我们是不是应该再讨论一下
示例输出3：
我觉得这个方案还是有一些问题的。

首先，成本太高。其次，时间上来不及。你觉得呢？我们是不是应该再讨论一下？
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
        # Strip any markdown code fences the model might add
        result = result.strip()
        if result.startswith("```"):
            lines = result.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            result = "\n".join(lines).strip()
        return jsonify({'polished_text': result})
    except openai.APIStatusError as e:
        if e.status_code == 402:
            return jsonify({'error': 'API 额度已用尽 (402 USD spend limit exceeded)，请在 OpenRouter 充值或等待额度重置'}), 402
        return jsonify({'error': f'API 错误: {str(e)}'}), e.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

app_name = app
