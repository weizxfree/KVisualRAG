<div align="center">
  <img src="./assets/logo.png" width="300" height="300" />
</div>

<p align="center">
  <a href="./README.md">English</a> |
  <a href="./README_zh.md">简体中文</a>
</p>

# 🌌 KVisualRAG：视觉驱动的RAG，超越OCR

> **忘记分词。忘记布局丢失。**  
> 借助纯视觉嵌入，KVisualRAG 能像人一样理解文档——逐页扫描，理解结构及所有内容。

**KVisualRAG** 是一款由**纯视觉嵌入**驱动的下一代检索增强生成（RAG）系统。它将文档视为视觉结构化对象，而不仅仅是token序列，从而保留布局、语义以及表格、图表等图形元素。

KVisualRAG 专为研究和企业部署而设计，具有以下特性：

- 🧑‍💻 **现代前端**：[Next.js 15](https://nextjs.org/blog/next-15)、[TailwindCSS 4.0](https://tailwindcss.com)、TypeScript
- ⚙️ **异步后端**：[FastAPI](https://github.com/fastapi/fastapi)，采用 **Redis**、**MySQL**、**MongoDB**、**MinIO** 的异步堆栈
- 🧠 **视觉多模态基础**：默认使用 [Qwen2.5-VL](https://github.com/QwenLM/Qwen2.5-VL) 作为大语言模型，未来支持 **GPT-4o**、**Claude**、**Gemini**
- 🎯 **图像级嵌入**：通过 [Colpali](https://github.com/illuin-tech/colpali) + [colqwen2.5](https://huggingface.co/vidore/colqwen2.5-v0.2) 生成丰富的语义向量，存储于 [Milvus](https://milvus.io/)

> KVisualRAG 旨在成为一个**企业级、即插即用的视觉RAG平台**，连接非结构化文档理解与多模态AI。

---

## 📚 目录

- [最新更新](#-最新更新)
- [为何选择KVisualRAG？](#-为何选择kvisualrag)
- [首个试用版本](#-首个试用版本)
- [系统架构](#-系统架构)
- [主要特性](#-主要特性)
- [技术栈](#-技术栈)
- [部署](#-部署)
- [应用场景](#-应用场景)
- [路线图](#-路线图)
- [贡献](#-贡献)
- [联系方式](#-联系方式)
- [许可证](#-许可证)

---

## 🚀 最新更新

- **(2025.5.26) 首个试用版本发布**：上传PDF文档，提问并获得保留布局的答案。未来计划详见[路线图](#-路线图)。
- **当前特性**：
  - PDF批量上传与解析
  - LiteLLm 集成，支持 Ollama 和 OpenAPI 兼容协议
  - 视觉驱动的RAG文档问答
  - 优化的后端：**FastAPI**、**Milvus**、**Redis**、**MongoDB**、**MinIO**
- **即将推出**：
  -更多文档格式（Word、PPT、Excel、图像）
  - 更多大语言模型（GPT-4o、Claude）
  - 用于多跳推理的智能代理

---

## ❓ 为何选择KVisualRAG？

大多数RAG系统依赖OCR或文本解析，这会导致：

- ❌ **布局丢失**（列、表格、层次结构）
- ❌ **不支持非文本视觉元素**（图表、图像）
- ❌ **OCR分段导致的语义中断**

**KVisualRAG改变了这一切。**

> 🔍 它能像人类读者一样，从整体上理解每个页面。

借助**纯视觉嵌入**，KVisualRAG能够保留：
- ✅ 布局（标题、列表、段落）
- ✅ 表格完整性（行、列、合并单元格）
- ✅ 视觉元素（图表、手写内容）
- ✅ 布局与内容的一致性

---

## 🧪 首个试用版本

> ✅ **首个版本已发布！**  
> 上传您的PDF，提问并获得保留布局的答案。

### 截图

1. **首页**
   ![首页](./assets/homepage.png)
2. **知识库**
   ![知识库](./assets/knowledgebase.png)
3. **交互式问答**
   ![对话1](./assets/dialog1.png)
   ![对话](./assets/dialog.png)

---

## 🧠 系统架构

KVisualRAG的流程设计遵循**异步优先**、**视觉驱动**和**可扩展**的原则。

### 查询流程
嵌入 → 向量检索 → 答案生成

![查询架构](./assets/query.png)

### 上传与索引流程
PDF → 图像 → 视觉嵌入 (ColQwen2.5) → 元数据与存储

![上传架构](./assets/upload.png)

---

## ✨ 主要特性

| 特性                 | 描述                                       |
|------------------------|--------------------------------------------|
| 🧠 视觉驱动的RAG        | 无需OCR，直接进行图像嵌入                   |
| 🧾 保留布局的问答       | 理解表格、标题、多栏布局                      |
| 📊 视觉内容支持         | 处理图表、图示、非文本元素                    |
| ⚙️ 异步解析            | 通过Kafka进行后台文档处理                   |
| 🔍 快速向量搜索         | 使用Milvus实现可扩展的密集向量检索             |
| 🤖 灵活的LLM后端       | Qwen2.5-VL，可扩展至GPT-4o、Claude等        |
| 🌐 现代Web UI          | Next.js + TypeScript + TailwindCSS + Zustand |

---

## 🧰 技术栈

**前端**：  
Next.js、TypeScript、TailwindCSS、Zustand

**后端**：  
FastAPI、Kafka、Redis、MySQL、MongoDB、MinIO、Milvus

**模型**：  
嵌入：colqwen2.5-v0.2  
大语言模型：Qwen2.5-VL系列

---

## 🚀 部署

### ▶️ 本地开发

```bash
# 克隆仓库
git clone https://github.com/weizxfree/KVisualRAG
cd KVisualRAG

# 配置环境
nvim .env
nvim web/.env.local
nvim gunicorn_config.py
# 或使用默认设置

# 启动依赖项 (Milvus, Redis, MongoDB, Kafka, MinIO)
cd docker
sudo docker-compose -f milvus-standalone-docker-compose.yml -f docker-compose.yml up -d
cd ../

# Python 环境 (可选)
# python -m venv venv && source venv/bin/activate
# 或使用 conda
conda create --name KVisualRAG python=3.10
conda activate KVisualRAG

# 系统依赖 (Ubuntu/Debian)
sudo apt-get update && sudo apt-get install -y poppler-utils
# Fedora/CentOS:
# sudo dnf install -y poppler-utils

# 安装Python依赖
pip install -r requirements.txt

git lfs install

# 下载基础模型权重
git clone https://huggingface.co/vidore/colqwen2.5-base
# 中国用户：
# git clone https://hf-mirror.com/vidore/colqwen2.5-base

# 下载LoRA微调权重
git clone https://huggingface.co/vidore/colqwen2.5-v0.2
# 中国用户：
# git clone https://hf-mirror.com/vidore/colqwen2.5-v0.2

# 修改 \`colqwen2.5-v0.2/adapter_config.json\` 中的 \`base_model_name_or_path\` 字段
base_model_name_or_path="/absolute/path/to/colqwen2.5-base"
# 设置为colqwen2.5-base的本地路径

# 在您的 .env 文件中设置以下内容
COLBERT_MODEL_PATH="/absolute/path/to/colqwen2.5-v0.2"

# 初始化MySQL数据库
alembic init migrations
cp env.py migrations
alembic revision --autogenerate -m "Init Mysql"
alembic upgrade head

# 启动后端
gunicorn -c gunicorn_config.py app.main:app
# 或: nohup gunicorn -c gunicorn_config.py app.main:app > gunicorn.log 2>&1 &
# http://localhost:8000

# 启动嵌入服务器
python model_server.py

# 前端
cd web
npm install
npm run dev # http://localhost:3000
# 或构建: npm run build && npm start
```

> 🧪 注意：Milvus、Redis、MongoDB、Kafka、MinIO 必须在本地或通过Docker运行。

---

## 📚 应用场景

- 🧾 **智能文档问答**：合同、发票、扫描报告
- 🏛 **政策/法律文件**：复杂PDF解析
- 🏭 **工业手册**：OCR不友好的布局、表格、图表
- 📈 **视觉分析**：从图表中挖掘趋势

---

## 📦 路线图

- [x] PDF批量上传与解析
- [x] 基于RAG的对话系统
- [x] OpenAI兼容API (ollama, sglang, vllm)
- [ ] 代码模块化与可扩展性
- [ ]更多视觉/多模态大语言模型
- [ ] 更多文档格式（Word、PPT、Excel）
- [ ] Docker Compose部署
- [ ] 公共知识库API

---

## 🤝 贡献

欢迎贡献！请随时提出issue或pull request。  
CONTRIBUTING.md 即将推出，其中包含代码贡献指南和最佳实践。

---

## 📫 联系方式

**KnowFlow 企业知识库**  
🐙 [github.com/weizxfree/KVisualRAG](https://github.com/weizxfree/KVisualRAG)  
🔍 微信公众号：KnowFlow 企业知识库

---

## 📄 许可证

本项目采用 **Apache 2.0 许可证**。详情请参阅[LICENSE](./LICENSE)文件。

---

> _KVisualRAG能识别OCR无法识别的内容。它像我们一样阅读文档——视觉化、结构化、整体化。_
