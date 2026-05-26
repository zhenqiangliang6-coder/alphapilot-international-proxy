AlphaPilot International Proxy（国际模型中转层）
Production‑grade Model Proxy Layer for Google Gemini / HF Agents / OpenAI / Multi‑Agent Systems

🚀 项目简介（Project Overview）
AlphaPilot International Proxy 是 AlphaPilot OS V4 的核心基础设施之一。
它的使命是：

在中国大陆环境下，为 AlphaPilot OS 提供稳定、统一、可扩展的国际模型访问能力。

由于中国大陆无法直接访问 Google Gemini、OpenAI、HuggingFace Agents 等国际模型，本项目通过 Render（Python 3 Runtime） 部署一个轻量级、生产级的 FastAPI 中转层，实现：

统一模型调用接口

统一消息格式

统一流式输出（SSE）

统一错误处理

统一模型路由

统一安全策略

最终形成：

Code
AlphaPilot OS（中国大陆）
        ↓
AlphaPilot International Proxy（Render，美国）
        ↓
Google Gemini / HuggingFace Agents / OpenAI / 其它智能体
🧠 为什么选择 Render？
Render 是目前最适合做“国际模型中转层”的平台：

✔ 免费（Free Tier 足够使用）

✔ 支持 Python 3 Runtime

✔ 支持 FastAPI

✔ 支持环境变量（安全存储 API Key）

✔ 支持公网 HTTPS

✔ 在中国大陆访问稳定

✔ 与 Google Gemini（美国区域）延迟最低

✔ 不需要 Docker（更轻量）

🌍 备用节点（可随时扩展）
为了保证高可用性，本项目设计为 多节点可部署：

平台	状态	说明
Render（主节点）	✔ 推荐	最稳定、最适合 Python 3 Runtime
Fly.io（备用）	✔ 可用	全球边缘节点，适合高性能代理
HuggingFace Spaces（备用）	✔ 可用	Docker 方式部署，适合轻量代理
Railway（备用）	✔ 可用	免费额度足够，部署简单
Deta Space（备用）	✔ 可用	适合非流式代理


本 README 的结构设计，使得任何节点都能直接部署。

🏗 项目结构（Production‑grade）
Code
alphapilot-international-proxy/
│
├── main.py                 # FastAPI 主入口（统一路由）
├── google_adapter.py       # Google Gemini 适配器（生产级）
├── requirements.txt        # Python 依赖
├── render.yaml             # Render 部署配置（可选）
│
└── README.md               # 本文档
🔌 统一接口规范（OpenAI-Compatible）
所有模型统一走：

Code
POST /v1/chat/completions
请求格式（与 OpenAI 完全兼容）：

json
{
  "model": "google/gemini-2.0-pro",
  "messages": [
    {"role": "user", "content": "Hello"}
  ],
  "stream": true
}
响应格式（与 OpenAI 完全兼容）：

非流式：choices[].message.content

流式：delta.content

这意味着：

AlphaPilot OS 不需要为不同模型写不同逻辑。
所有模型都通过中转层统一格式输出。

🔧 核心文件说明
main.py
FastAPI 主入口

统一路由 /v1/chat/completions

自动识别模型前缀（如 google/）

调用对应适配器

google_adapter.py
将 OpenAI 风格 messages → 转为 Gemini 风格 contents

调用 Google Gemini API

将 Gemini 输出 → 转为 OpenAI 风格 delta

支持流式（SSE）与非流式

requirements.txt
FastAPI

Uvicorn

httpx

python-dotenv

render.yaml（可选）
Render 自动部署配置

指定 Python 版本、启动命令、环境变量等

🔐 环境变量（Render）
在 Render 的 Environment Variables 中添加：

Code
GOOGLE_API_KEY = <你的 Gemini API Key>
🚀 部署步骤（Render Python 3 Runtime）
创建 GitHub 仓库：alphapilot-international-proxy

上传本项目文件

登录 Render → New → Web Service

选择 GitHub 仓库

配置：

Runtime: Python 3

Build Command: pip install -r requirements.txt

Start Command: uvicorn main:app --host 0.0.0.0 --port 10000

添加环境变量 GOOGLE_API_KEY

Deploy

部署完成后，你会得到一个 URL，例如：

Code
https://alphapilot-proxy.onrender.com
🔥 本地 AlphaPilot OS 如何调用？
只需要在模型路由中添加：

python
if model.startswith("google/"):
    url = "https://alphapilot-proxy.onrender.com/v1/chat/completions"
然后即可使用：

Code
model: "google/gemini-2.0-pro"
🧩 未来扩展（V4 核心能力）
本中转层将扩展支持：

HuggingFace Agents

OpenAI GPT 系列

DeepSeek（海外版）

Anthropic Claude

自定义智能体（AlphaPilot Agents）

多模型路由（Model Router）

多智能体协作（Multi-Agent Protocol）

所有扩展都通过新增 adapter 文件实现：

Code
adapters/
  ├── google_adapter.py
  ├── openai_adapter.py
  ├── hf_agents_adapter.py
  └── deepseek_adapter.py
🏁 总结
本项目是 AlphaPilot OS V4 的国际化基础设施，提供：

稳定

统一

可扩展

可维护

可被任何智能体理解

的国际模型访问能力。

这是你未来构建 全球级 AI 编程操作系统 的关键一步。