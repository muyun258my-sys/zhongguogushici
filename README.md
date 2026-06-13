# 中国古诗词智能问答助手

一个基于 `FastAPI + LangChain + Chroma` 的中国古诗词智能问答助手 MVP。

当前项目按 `Python 3.14.6` 运行约束进行维护和验证。

项目特点：

- 支持古诗词问答、释义、赏析、名句反查
- 支持按主题推荐，如思乡、送别、月、边塞
- 使用 LangChain 组织提示词、检索和问答链路
- 使用 Chroma 做本地向量检索
- 未配置大模型密钥时，仍可使用降级版规则回答

## 目录结构

```text
.
├── app
│   ├── rag
│   ├── services
│   ├── web
│   ├── config.py
│   ├── main.py
│   ├── models.py
│   └── prompts.py
├── data
│   └── poems.json
├── scripts
│   └── ingest.py
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
├── requirements.lock.txt
└── .python-version
```

## 功能范围

当前版本支持：

- 作品信息问答
- 诗句释义与简要赏析
- 主题推荐
- 会话式连续提问
- 检索结果出处返回

## 环境准备

当前版本仅按 `Python 3.14.6` 进行验证。建议使用：

- `C:\Users\ASUS\AppData\Local\Python\pythoncore-3.14-64\python.exe`

首次进入项目时，先检查解释器与 ABI 是否正确：

```powershell
python -c "import sys; print(sys.version); print(sys.executable)"
python -c "import pydantic_core._pydantic_core as c; print(c.__file__)"
```

注意：要检查的是 `pydantic_core._pydantic_core` 这个**二进制扩展**的文件名（形如 `_pydantic_core.cp314-win_amd64.pyd`），不是 `pydantic_core.__file__`（那永远指向包的 `__init__.py`）。如果第二条命令输出的文件名里不包含 `cp314-win_amd64`，说明环境已混装，需要重建虚拟环境。

1. 创建虚拟环境

```powershell
python -m venv .venv
```

2. 激活虚拟环境

```powershell
.\.venv\Scripts\Activate.ps1
```

3. 安装依赖

```powershell
python -m pip install --upgrade pip setuptools wheel
python -m pip install --force-reinstall --no-cache-dir -r requirements.txt
```

4. 配置环境变量

```powershell
Copy-Item .env.example .env
```

如果你使用 OpenAI 兼容接口，请在 `.env` 中填写：

- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `LLM_MODEL_NAME`
- `EMBEDDING_MODEL_NAME`

如果不填密钥，项目仍可启动，但会使用降级版回答逻辑，不能发挥完整生成能力。

## 环境自检

安装依赖后，先执行环境自检：

```powershell
python scripts/check_env.py
```

这条命令会检查：

- Python 主次版本是否为 `3.14`
- `fastapi`、`pydantic`、`pydantic_core` 是否可导入
- `pydantic_core` 的二进制扩展是否为 `cp314`

## 坏环境修复流程

如果你遇到下面这些报错：

- `No module named 'pydantic_core._pydantic_core'`
- `Unable to create process using ... .venv\\Scripts\\python.exe`
- `uvicorn` 启动时导入 `fastapi/pydantic` 失败

按下面的顺序修复：

1. 删除旧虚拟环境

```powershell
Remove-Item -Recurse -Force .venv
```

2. 用 Python 3.14 重新创建虚拟环境

```powershell
python -m venv .venv
```

3. 激活虚拟环境

```powershell
.\.venv\Scripts\Activate.ps1
```

4. 升级安装工具并无缓存重装依赖

```powershell
python -m pip install --upgrade pip setuptools wheel
python -m pip install --force-reinstall --no-cache-dir -r requirements.txt
```

5. 运行环境检查

```powershell
python scripts/check_env.py
```

6. 如果安装成功，生成本机锁定依赖文件

```powershell
python -m pip freeze > requirements.lock.txt
```

7. 最后启动服务

```powershell
uvicorn app.main:app --reload
```

## 数据入库

首次使用建议先执行向量化入库：

```powershell
python scripts/ingest.py
```

如果你在 `.env` 中将 `AUTO_INGEST_ON_START=true`，服务首次启动时也会自动尝试入库。

## 导入 chinese-poetry 知识库

项目支持从 [chinese-poetry/chinese-poetry](https://github.com/chinese-poetry/chinese-poetry) 导入开源古诗词数据。

1. 克隆数据仓库

```powershell
New-Item -ItemType Directory -Force external
git clone https://github.com/chinese-poetry/chinese-poetry.git external/chinese-poetry
```

2. 导入唐诗和宋词，默认每类最多导入 2000 条

```powershell
python scripts/import_chinese_poetry.py
```

如果你已经把数据仓库放在项目根目录的 `chinese-poetry` 文件夹中，使用：

```powershell
python scripts/import_chinese_poetry.py --source-dir .\chinese-poetry
```

3. 导入指定集合

```powershell
python scripts/import_chinese_poetry.py --dataset tang --dataset song-ci --dataset shijing --dataset chuci
```

4. 不限制数量导入

```powershell
python scripts/import_chinese_poetry.py --limit 0
```

导入脚本会把数据合并进 `data/poems.json`，并跳过重复的 `title + author + content` 记录。

如果你已配置 `OPENAI_API_KEY` 并需要更新向量库，导入后重新执行：

```powershell
python scripts/ingest.py
```

## 启动服务

```powershell
uvicorn app.main:app --reload
```

启动后访问：

- 首页：[http://127.0.0.1:8000](http://127.0.0.1:8000)
- 健康检查：[http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
- API 文档：[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## API 示例

请求：

```bash
curl -X POST "http://127.0.0.1:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d "{\"question\":\"推荐几首写月亮的唐诗\",\"session_id\":\"demo\"}"
```

返回示例：

```json
{
  "answer": "可以先读《静夜思》《望月怀远》《山居秋暝》...",
  "question_type": "recommend",
  "used_llm": true,
  "sources": [
    {
      "title": "静夜思",
      "author": "李白",
      "dynasty": "唐",
      "source": "内置示例古诗词数据集"
    }
  ]
}
```

## 推荐的下一步

你可以继续扩展这些方向：

- 补充更大规模的古诗词数据集
- 为诗词增加更细的标签体系
- 增加重排序和混合检索
- 引入用户画像与个性化推荐
- 添加后台管理页面，支持导入新诗词

## 锁定依赖

`requirements.txt` 仍然是安装入口。

当你在本机完成一次通过 `scripts/check_env.py` 的安装后，建议立刻生成：

```powershell
python -m pip freeze > requirements.lock.txt
```

这样后续就可以优先基于 `requirements.lock.txt` 重建环境，减少 ABI 混装和依赖漂移。
