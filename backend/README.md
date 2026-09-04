# 后端部署教程

在启动后端服务之前, 需要先安装好依赖, 并申请 Gemini API Key 以及一个 S3 兼容的对象存储服务(推荐 Cloudflare R2)。

**注意 ⚠️： 请至少保证你本地的 Python 版本为 3.9 及以上, 否则可能会出现依赖无法安装, 项目启动失败等问题。**

链接转写功能依赖 `ffmpeg`, 本地运行前请确保系统已安装 `ffmpeg`(Docker 镜像中已内置)。

## 1. 安装依赖
```bash
pip install -r requirements.txt
```

## 2. 配置环境变量

```bash
# 主用服务商: Google Gemini(转写与图文生成都会先调用它)
export GEMINI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
export GEMINI_MODEL_ID=gemini-3.6-flash
export GEMINI_API_KEY=xxxx

# 可选的备用服务商: OpenRouter
export OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
export OPENROUTER_MODEL_ID=openai/gpt-4o-mini
export OPENROUTER_API_KEY=xxxx

# S3 兼容对象存储(例如 Cloudflare R2)
export STORAGE_ACCESS_KEY=xxxx
export STORAGE_SECRET_KEY=xxxx
export STORAGE_ENDPOINT=xxxx
export STORAGE_REGION=auto
export STORAGE_BUCKET=xxxx

export WEB_ACCESS_PASSWORD=xxx
```

环境变量说明:

**GEMINI_API_KEY / GEMINI_MODEL_ID**【必填】: 在 [Google AI Studio](https://aistudio.google.com/) 创建 API Key, 并选择支持音频输入的模型。

**OPENROUTER_API_KEY / OPENROUTER_MODEL_ID**【选填】: Gemini 调用失败时的备用服务商。注意 `openai/gpt-4o-mini` 是付费模型, 若需免费额度请使用带 `:free` 后缀的模型。

**STORAGE_\***【必填】: S3 兼容对象存储配置, 需要为存储桶添加允许 `http://localhost:5173` 的跨域规则。

**WEB_ACCESS_PASSWORD**【选填】: 前端访问后端服务的密码, 后端指定之后需要在前端自定义设置-> 访问密码填写该密码才可以正常使用。

## 3. 启动服务
```bash
python app.py
```

## 接口说明

- `POST /api/v1/audio/transcription-tasks` — 上传后的音频转写(自动识别语种, 保持原始语言)
- `GET /api/v1/audio/transcription-tasks/{task_id}` — 查询转写结果
- `POST /api/v1/link/transcription-tasks` — 通过视频/网页链接转写(使用 yt-dlp 抓取音轨)
- `POST /api/v1/llm/translation` — 将转写文本翻译为目标语言
- `POST /api/v1/llm/markdown-generation` — 生成图文内容, 可传 `target_language` 指定输出语言

### FAQ
- ❓: 如何使用 ChatGPT, Claude 等第三方大模型。
- 后端统一使用 OpenAI SDK 调用。你可以把 `OPENROUTER_BASE_URL`, `OPENROUTER_API_KEY` 和 `OPENROUTER_MODEL_ID` 替换成任意 OpenAI 兼容的服务商。注意音频转写需要服务商支持音频输入。
