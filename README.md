# 中国古诗词智能问答助手

基于 `FastAPI + LangChain + Chroma` 构建的古诗词问答助手。项目支持作品查询、名句反查、诗词赏析、主题推荐和作者作品列表，并可导入 `chinese-poetry/chinese-poetry` 数据集扩展知识库。

当前项目按 `Python 3.14.6` 验证。

## 功能亮点

- 古诗词问答：查询作者、朝代、出处、原文等基础信息。
- 名句反查：例如“东风夜放花千树出自哪一首”。
- 赏析与释义：解释诗句含义、意象和情感。
- 主题推荐：按思乡、送别、月、边塞等主题推荐作品。
- 作者作品列表：例如“李白的诗词有哪些”，只返回作品名。
- 本地兜底：未配置大模型或外部接口失败时，仍可使用本地知识库回答。

## 技术栈

- `FastAPI`：Web 服务与接口
- `LangChain`：提示词、模型调用和检索链路
- `Chroma`：本地向量库
- `python-dotenv`：环境变量管理
- `chinese-poetry/chinese-poetry`：可选外部古诗词数据来源

## 项目结构

```text
.
├── app
│   ├── main.py                  # FastAPI 入口
│   ├── config.py                # 配置读取
│   ├── models.py                # 请求/响应模型
│   ├── prompts.py               # 大模型提示词
│   ├── rag
│   │   ├── repository.py        # 本地知识库检索
│   │   └── vectorstore.py       # Chroma 向量检索
│   ├── services
│   │   └── poetry_assistant.py  # 问答主逻辑
│   └── web
│       └── index.html           # 简单聊天页面
├── data
│   └── poems.json               # 项目知识库
├── scripts
│   ├── check_env.py             # 环境检查
│   ├── import_chinese_poetry.py # 导入 chinese-poetry 数据
│   ├── ingest.py                # 重建向量库
│   └── start_server.ps1         # Windows 启动脚本
├── external
│   └── README.md                # 第三方数据放置说明
├── requirements.txt
├── .env.example
└── .python-version
```

## 快速开始

### 1. 创建并激活虚拟环境

```powershell
cd C:\Users\ASUS\Desktop\xiangmu
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. 安装依赖

```powershell
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
```

如果你之前遇到过 `pydantic_core` ABI 混装问题，可以无缓存重装：

```powershell
python -m pip install --force-reinstall --no-cache-dir -r requirements.txt
```

### 3. 配置环境变量

```powershell
Copy-Item .env.example .env
```

如果暂时没有模型密钥，也可以不填，项目会使用本地规则兜底回答。

### 4. 检查环境

```powershell
python scripts/check_env.py
```

通过后会看到 `Environment check passed.`。

### 5. 启动服务

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

启动后访问：

- 首页：<http://127.0.0.1:8000>
- 健康检查：<http://127.0.0.1:8000/health>
- API 文档：<http://127.0.0.1:8000/docs>

停止服务时，在运行服务的终端里按 `Ctrl+C`。

## 环境变量

`.env.example` 提供了所有可配置项：

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=
LLM_MODEL_NAME=gpt-4o-mini
EMBEDDING_MODEL_NAME=text-embedding-3-small
TOP_K=4
AUTO_INGEST_ON_START=false
```

配置说明：

- `OPENAI_API_KEY`：OpenAI 兼容接口密钥。
- `OPENAI_BASE_URL`：自定义模型服务地址。使用官方 OpenAI 时可留空。
- `LLM_MODEL_NAME`：聊天模型名称。
- `EMBEDDING_MODEL_NAME`：向量化模型名称。
- `TOP_K`：每次检索返回的候选数量。
- `AUTO_INGEST_ON_START`：服务启动时是否自动尝试重建向量库。

注意：`.env` 已被 `.gitignore` 忽略，不要把真实密钥提交到 GitHub。

## 知识库

项目默认知识库存放在：

```text
data/poems.json
```

每条数据结构如下：

```json
{
  "id": "qing-yu-an-yuan-xi",
  "title": "青玉案·元夕",
  "author": "辛弃疾",
  "dynasty": "宋",
  "content": "东风夜放花千树。更吹落、星如雨。...",
  "translation": "元宵夜里，东风仿佛吹开了千万树繁花...",
  "annotation": "“东风夜放花千树”写元宵灯火和烟花盛景。",
  "appreciation": "全词上片极写元宵繁华热闹...",
  "tags": ["宋词", "元宵", "灯火", "辛弃疾", "名句"],
  "source": "人工补充：青玉案·元夕"
}
```

新增知识时，保持 `id` 唯一即可。`tags` 会影响主题推荐效果。

## 导入 chinese-poetry 数据

项目支持从 [chinese-poetry/chinese-poetry](https://github.com/chinese-poetry/chinese-poetry) 导入唐诗、宋词、诗经、楚辞。

如果数据仓库在项目根目录的 `chinese-poetry` 文件夹中：

```powershell
python scripts/import_chinese_poetry.py --source-dir .\chinese-poetry
```

如果想把数据仓库放在 `external/chinese-poetry`：

```powershell
New-Item -ItemType Directory -Force external
git clone https://github.com/chinese-poetry/chinese-poetry.git external/chinese-poetry
python scripts/import_chinese_poetry.py
```

常用导入命令：

```powershell
# 默认导入唐诗和宋词，每类最多 2000 条
python scripts/import_chinese_poetry.py --source-dir .\chinese-poetry

# 导入指定集合
python scripts/import_chinese_poetry.py --source-dir .\chinese-poetry --dataset tang --dataset song-ci --dataset shijing --dataset chuci

# 不限制数量
python scripts/import_chinese_poetry.py --source-dir .\chinese-poetry --limit 0
```

导入脚本会合并到 `data/poems.json`，并跳过重复的 `title + author + content` 记录。

## 向量库

项目默认使用本地开源 Embedding 模型：

```env
EMBEDDING_PROVIDER=local
LOCAL_EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5
LOCAL_EMBEDDING_CACHE_DIR=models/embedding
```

首次使用本地模型前，先安装依赖并下载模型：

```powershell
python -m pip install -r requirements.txt
python scripts/download_embedding_model.py
```

下载完成后，模型会保存在：

```text
models/embedding/BAAI--bge-small-zh-v1.5
```

然后重建 Chroma 向量库：

```powershell
python scripts/ingest.py
```

向量库默认保存在：

```text
storage/chroma
```

如果外部 Embedding 接口不可用，项目仍会退回本地规则检索，不会影响基础问答。

如果你想改回外部 OpenAI 兼容 Embedding，可以把 `.env` 改成：

```env
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL_NAME=text-embedding-3-small
```

## API 示例

```powershell
Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/api/chat" `
  -Method Post `
  -ContentType "application/json" `
  -Body '{"question":"东风夜放花千树出自哪一首","session_id":"demo"}'
```

返回字段：

```json
{
  "answer": "结论：这个问题可以先参考《青玉案·元夕》这首作品。...",
  "question_type": "lookup",
  "used_llm": true,
  "sources": [
    {
      "title": "青玉案·元夕",
      "author": "辛弃疾",
      "dynasty": "宋",
      "source": "人工补充：青玉案·元夕"
    }
  ],
  "contexts": []
}
```

## 常见问题

**启动时报 `No module named 'pydantic_core._pydantic_core'`**

这是虚拟环境中二进制依赖和 Python 版本不匹配。重建虚拟环境即可：

```powershell
Remove-Item -Recurse -Force .venv
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
python -m pip install --force-reinstall --no-cache-dir -r requirements.txt
python scripts/check_env.py
```

**页面显示“请求失败”**

通常是后端服务没有启动，或浏览器还连着旧进程。重新启动：

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

**问作者作品时为什么只返回名字？**

这是项目的明确行为：例如“李白的诗词有哪些”只返回作品名，避免出现冗余解释。

**DeepSeek 或其他 OpenAI 兼容接口能用吗？**

聊天模型可以使用 OpenAI 兼容接口，但 Embedding 模型要确保服务商支持对应模型名。若 Embedding 失败，系统会自动退回本地检索。

## 维护建议

- 扩展知识库后，优先确认 `data/poems.json` 可被正常读取。
- 如果启用向量检索，导入新数据后重新执行 `python scripts/ingest.py`。
- 提交 GitHub 前确认 `.env`、`.venv/`、`storage/`、`chinese-poetry/` 没有被提交。
- 稳定运行后可生成本机锁定文件：

```powershell
python -m pip freeze > requirements.lock.txt
```
