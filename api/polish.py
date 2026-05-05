from openai import OpenAI
import os
import json

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

def handler(request):
    # Handle CORS preflight
    if request.method == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type",
            },
            "body": ""
        }
    
    # Only accept POST
    if request.method != "POST":
        return {
            "statusCode": 405,
            "body": json.dumps({"error": "Method not allowed"}),
            "headers": {"Content-Type": "application/json"}
        }
    
    try:
        # Parse request
        body = json.loads(request.body)
        user_text = body.get("text", "")
        
        if not user_text:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing 'text' field"}),
                "headers": {"Content-Type": "application/json"}
            }
        
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
        
        # Return polished text
        return {
            "statusCode": 200,
            "body": json.dumps({"polished_text": polished_text}),
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            }
        }
        
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)}),
            "headers": {"Content-Type": "application/json"}
        }
