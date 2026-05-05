# Typeless AI Service

一个类Typeless的语音润色服务API，使用OpenRouter免费模型。

## 功能

- 🎙️ 接收原始文本
- ✨ 调用OpenRouter免费LLM进行润色
- 📝 返回结构化、书面化的润色文本

## API 使用

### POST /api/polish

**请求:**
```json
{
  "text": "嗯，那个我想说一下，今天天气真不错..."
}
```

**响应:**
```json
{
  "polished_text": "一、天气与出行考量\n今日天气晴朗..."
}
```

## 部署

### 1. 推送到GitHub

```bash
# 在GitHub创建新仓库: typeless-ai-service
git remote add origin https://github.com/YOUR_USERNAME/typeless-ai-service.git
git push -u origin main
```

### 2. 部署到Vercel

1. 登录 [Vercel](https://vercel.com)
2. 点击 "New Project"
3. 导入 `typeless-ai-service` 仓库
4. 设置环境变量：
   - `OPENROUTER_API_KEY`: 你的OpenRouter API Key
5. 点击 "Deploy"

### 3. 测试

```bash
curl -X POST https://your-app.vercel.app/api/polish \
  -H "Content-Type: application/json" \
  -d '{"text": "嗯，那个我想说一下，今天天气真不错..."}'
```

## Tasker + AutoInput 配置

已提供 `tasker_autoinput_config.tsk` 配置文件。

### 导入步骤:

1. 将 `.tsk` 文件传到手机: `scp tasker_autoinput_config.tsk 100.90.147.17:/sdcard/Download/`
2. 打开Tasker → 菜单 → 导入配置文件
3. 授权无障碍服务、悬浮窗权限
4. 安装AutoInput插件 (Google Play)
5. 修改API地址为你的Vercel部署地址

## 技术栈

- Vercel Serverless Functions
- OpenRouter API (meta-llama/llama-3.3-8b-instruct:free)
- Tasker + AutoInput (Android自动化)
