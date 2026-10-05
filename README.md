# persona-chat 数字生命

把你的「人格 md 分层次」上传，用户就能跟「数字的你」聊天。后端调用 DeepSeek，基于你的性格/经历/语气等多层人格文件模拟你的说话方式。

## 功能

- **人格分层管理**：性格、经历、语气、知识库等多层 md，按权重控制生效程度
- **流式聊天**：AI 回复逐字输出，类 ChatGPT 体验
- **移动端优先**：手机微信内分享二维码即可打开

## 项目结构

```
persona-chat/
├── app/
│   ├── main.py            # FastAPI 入口
│   ├── config.py          # 配置（DeepSeek key 等）
│   ├── database.py        # SQLite 连接
│   ├── models.py          # 数据模型（人名层 / 聊天记录）
│   ├── routers/
│   │   ├── chat.py        # 聊天 API（流式）
│   │   └── persona.py     # 人格分层管理 API
│   └── services/
│       └── llm.py         # 人格拼接 + DeepSeek 调用
├── frontend/
│   ├── index.html         # 移动端聊天页
│   ├── style.css
│   └── app.js
├── data/                  # SQLite 数据文件（git 忽略）
├── requirements.txt
└── .env                   # 密钥配置（git 忽略，参考 .env.sample）
```

## 快速开始

```bash
# 1. 安装依赖
python3 -m venv --without-pip .venv
.venv/bin/python /path/to/get-pip.py   # 若 venv 无 pip
.venv/bin/pip install -r requirements.txt

# 2. 配置密钥
cp .env.sample .env
# 编辑 .env，填入你的 DEEPSEEK_API_KEY

# 3. 启动
.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 使用

1. 启动服务后打开 `http://localhost:8000`
2. 通过 API 上传人格层：
   ```bash
   curl -X POST http://localhost:8000/api/persona/layers \
     -H "Content-Type: application/json" \
     -d '{"name":"性格","type":"personality","content":"你的人格描述","weight":1.0}'
   ```
3. 在聊天页就能跟「数字的你」对话了

## API 一览

| 方法 | 路径 | 用途 |
|------|------|------|
| `POST` | `/api/chat/stream` | 流式聊天 |
| `GET` | `/api/persona/layers` | 人格层列表 |
| `POST` | `/api/persona/layers` | 新建人格层 |
| `DELETE` | `/api/persona/layers/{id}` | 删除人格层 |
