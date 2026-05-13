# 专利检索工具 — 方案设计文档 (Plan)

## 一、项目概述

构建一个智能专利检索工具，支持三大核心功能和两种检索模式：

### 核心功能

| 功能 | 描述 |
|------|------|
| **F1 — 专利意图解读** | 用户用自然语言描述想要检索的专利方向，AI 自动理解意图、扩展关键词语义、生成优化的检索式，返回相关专利列表 |
| **F2 — 专利号精准检索** | 用户输入专利号（支持多国格式：CN110123456A、US10123456B2、EP1234567B1、WO2020123456A1 等），系统精准定位并返回专利全文信息 |
| **F3 — 上传专利找相似** | 用户上传专利 PDF/DOCX/TXT 文档，系统提取文本内容，通过语义向量匹配检索出相似专利，并结合 AI 推理进行深度对比分析 |

### 检索方式

- **关键字检索**：基于 Elasticsearch 的 BM25 + 多字段匹配（标题、摘要、权利要求、发明人、IPC 分类号）
- **AI 推理检索**：基于 LLM 的多步代理式搜索（意图理解 → 查询扩展 → 多源检索 → 语义重排序 → 智能分析）

---

## 二、参考项目优点吸收

分析目录下 12 个开源项目后，各项目关键优点吸收如下：

| 参考项目 | 吸收的优点 |
|----------|-----------|
| **pqai** | 最成熟的 ML 管线：多后端向量索引（FAISS/Annoy/USearch）、CPC 子类预测缩小搜索空间、102（新颖性）/103（创造性）分别检索、ConceptMatch 重排序、可插拔架构 |
| **patents (PatentAI)** | 最现代的前端：Next.js + shadcn/ui、对话式专利搜索、本地 LLM 支持（Ollama/LM Studio）、Valyu API 语义搜索、沙盒化分析引擎 |
| **farfalle** | 最佳后端架构：Pro Search 多步代理（计划→搜索→聚合→回答）、搜索提供商抽象层（SearXNG/Tavily/Serper 可互换）、SSE 流式响应、Redis 缓存、Instructor 结构化输出 |
| **Vane** | 最完善的代理管线：分类→规划→搜索→爬取→写作，SessionManager 事件总线、多 LLM 注册中心、文件上传解析、SearXNG 本地化部署 |
| **OpenDeepSearch** | 最深的搜索能力：多跳 Pro 模式、语义重排序（Jina/Infinity+Qwen2-7B）、SmolAgents 集成、可插拔重排序器 |
| **patent_search** | 已验证的双模架构：Elasticsearch 关键字 + FAISS 语义向量混合搜索、SentenceTransformers 嵌入、Scrapy 专利爬虫管线 |
| **patent-similarity-rag** | 最简单的 LLM 驱动模式：LLM 生成优化检索词 → SerpAPI 查 Google Patents → LLM 语义相似度打分，适合快速原型 |
| **Rops** | EPO OPS API 的标准客户端实现，OAuth 令牌管理、批量查询、XML 解析 |
| **patzilla** | 多数据源适配器模式（6+ 专利机构）、企业级功能（卷宗管理、协作分享、多租户）、CLI + Web + API 三界面 |
| **302_patent_search** | 专利搜索 UI/UX 参考：多维度筛选（日期范围、语言、状态、类型、国家）、SSE 对话、PDF 处理 |
| **Awesome-Patent-Retrieval** | 专利数据源/API/数据集/论文的知识图谱索引，持续参考 |
| **public-apis** | 公共专利 API 目录（EPO、USPTO、PatentsView、TIPO）|

---

## 三、技术栈

### 后端

| 组件 | 技术 | 参考来源 |
|------|------|----------|
| 框架 | **Python FastAPI** + Uvicorn | pqai、farfalle |
| 搜索引擎 | **Elasticsearch** (BM25 关键字检索) | patent_search |
| 向量索引 | **FAISS** (主) + USearch (备) | pqai、patent_search |
| 嵌入模型 | **SentenceTransformers** (`all-MiniLM-L6-v2` / `BAAI/bge-large-zh-v1.5`) | pqai、patent_search |
| LLM 抽象层 | **LiteLLM** (支持 OpenAI / Anthropic / 本地 Ollama / 通义千问) | OpenDeepSearch、farfalle |
| 结构化输出 | **Instructor** + Pydantic | farfalle |
| 关系数据库 | **PostgreSQL** (生产) / SQLite (开发) | farfalle、Vane |
| ORM | **SQLAlchemy** + Alembic | farfalle |
| 缓存 | **Redis** (搜索结果缓存、速率限制) | farfalle |
| 文档解析 | **PyMuPDF** (PDF)、**python-docx**、**unstructured** | Vane |
| 异步任务 | **Celery** + Redis (专利数据爬取/索引) | — |
| 专利 API | **EPO OPS API**、**USPTO API**、**SerpAPI**（Google Patents） | Rops、public-apis |

### 前端

| 组件 | 技术 | 参考来源 |
|------|------|----------|
| 框架 | **Next.js 16** (App Router) + React 19 | patents、Vane |
| UI 组件 | **shadcn/ui** + Tailwind CSS 4 | patents、302_patent_search |
| 状态管理 | **Zustand** | patents |
| 数据请求 | **TanStack Query** | patents |
| 流式响应 | **SSE** (Server-Sent Events) | farfalle、Vane |
| 可视化 | **Recharts** (专利趋势/相似度图表) | patents |
| 国际化 | **i18next** (中文/英文) | 302_patent_search |
| 文件上传 | **react-dropzone** + 前端 PDF 预览 | — |

### 基础设施

| 组件 | 技术 |
|------|------|
| 容器化 | **Docker** + Docker Compose |
| 反向代理 | **Nginx** |
| 私有搜索 | **SearXNG**（可选，本地化隐私搜索） |

---

## 四、系统架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                        前端 (Next.js)                                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │
│  │ 专利搜索  │  │ 专利号   │  │ 上传比对  │  │ AI 对话面板      │   │
│  │ (F1)     │  │ 精准检索  │  │ (F3)     │  │ (SSE Streaming)  │   │
│  │          │  │ (F2)     │  │          │  │                  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘   │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ REST API + SSE
┌──────────────────────────────▼──────────────────────────────────────┐
│                      后端 (FastAPI)                                  │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                     API 路由层                                 │   │
│  │  /api/search/intent    /api/search/patent-number               │   │
│  │  /api/search/similar   /api/patent/{id}                       │   │
│  │  /api/upload/patent    /api/chat/stream                       │   │
│  └──────────────────────────┬───────────────────────────────────┘   │
│                             │                                        │
│  ┌──────────────────────────▼───────────────────────────────────┐   │
│  │                   代理搜索层 (Search Agent)                     │   │
│  │                                                                  │   │
│  │  ┌──────────┐  ┌──────────────┐  ┌────────────┐  ┌──────────┐ │   │
│  │  │ 意图理解  │→│ 查询扩展/规划 │→│ 多源并行检索│→│ 结果聚合  │ │   │
│  │  │(LLM)     │  │ (LLM+Prompt) │  │            │  │ +重排序   │ │   │
│  │  └──────────┘  └──────────────┘  └────────────┘  └──────────┘ │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                             │                                        │
│  ┌──────────────────────────▼───────────────────────────────────┐   │
│  │                    检索引擎层                                   │   │
│  │  ┌──────────────────────┐  ┌──────────────────────────┐      │   │
│  │  │ Elasticsearch        │  │ FAISS 向量索引            │      │   │
│  │  │ (关键字 BM25)        │  │ (语义相似度)              │      │   │
│  │  │ • 标题/摘要/权利要求  │  │ • SentenceTransformers   │      │   │
│  │  │ • IPC/CPC 分类       │  │ • 384/768维向量           │      │   │
│  │  │ • 发明人/申请人      │  │ • 近似最近邻搜索          │      │   │
│  │  └──────────────────────┘  └──────────────────────────┘      │   │
│  │              ↕ 混合检索 (Hybrid Search) ↕                     │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                             │                                        │
│  ┌──────────────────────────▼───────────────────────────────────┐   │
│  │                   数据获取层 (Data Access)                      │   │
│  │  ┌──────────┐  ┌──────────┐  ┌─────────┐  ┌──────────────┐  │   │
│  │  │ EPO OPS  │  │ USPTO    │  │ SerpAPI  │  │ 本地专利库    │  │   │
│  │  │ API      │  │ API      │  │(Google)  │  │ (爬虫+索引)  │  │   │
│  │  └──────────┘  └──────────┘  └─────────┘  └──────────────┘  │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                   数据存储层                                    │   │
│  │  ┌────────────┐  ┌──────────┐  ┌──────────┐  ┌───────────┐  │   │
│  │  │ PostgreSQL │  │ Redis    │  │ FAISS    │  │ S3/本地   │  │   │
│  │  │ 用户/历史  │  │ 缓存/队列 │  │ 向量索引  │  │ 文件存储  │  │   │
│  │  └────────────┘  └──────────┘  └──────────┘  └───────────┘  │   │
│  └────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 五、核心功能详细设计

### F1 — 专利意图解读（自然语言搜索）

**用户流程：**
1. 用户输入自然语言描述，如："一种基于深度学习的自动驾驶障碍物检测方法，使用多模态传感器融合"
2. AI 分析意图，提取核心技术特征
3. 自动扩展相关关键词、同义词、IPC 分类号
4. 执行混合检索（关键字 + 语义）
5. 返回高相关度专利列表，附带 AI 解读分析

**技术实现：**

```
输入: "一种基于深度学习的自动驾驶障碍物检测方法"

Step 1 — 意图解析 (LLM)
  ├─ 技术领域: 自动驾驶, 计算机视觉
  ├─ 核心特征: 深度学习, 障碍物检测, 多模态传感器融合
  ├─ 预测 IPC: G06V20/58, G06N3/08, B60W60/00
  └─ 扩展关键词: object detection, LiDAR, camera fusion, CNN, transformer

Step 2 — 多路检索
  ├─ Elasticsearch: 关键词 + IPC 布尔检索
  ├─ FAISS: 描述文本向量语义检索
  └─ Google Patents (SerpAPI): 补充检索

Step 3 — 结果融合与重排序
  ├─ RRF (Reciprocal Rank Fusion) 合并多路结果
  ├─ Cross-encoder 重排序 (可选)
  └─ LLM 最终相关性判断

Step 4 — AI 解读输出
  ├─ 相关专利列表 (标题/摘要/相似度/专利号)
  ├─ 技术分布分析 (主要申请人/IPC 分布)
  └─ AI 总结: 该领域技术现状概述
```

### F2 — 专利号精准检索

**用户流程：**
1. 用户输入专利号（自动识别格式）
2. 系统查询多数据源
3. 返回完整专利信息

**支持的格式：**
- CN 专利: `CN110123456A`, `CN110123456B`, `CN201910012345.6`
- US 专利: `US10123456B2`, `US20180123456A1`
- EP 专利: `EP1234567B1`, `EP1234567A1`
- WO 专利: `WO2020123456A1`
- JP 专利: `JP2020-123456A`

**技术实现：**

```
Step 1 — 专利号解析 & 标准化
  ├─ 正则识别国家/类型/编号
  └─ 标准化为统一格式

Step 2 — 多源查询（优先级递减）
  ├─ 本地数据库 (PostgreSQL, 已索引的专利)
  ├─ EPO OPS API (欧洲专利局)
  ├─ USPTO API (美国专利局)
  └─ Google Patents (SerpAPI 兜底)

Step 3 — 返回完整信息
  ├─ 著录项 (标题/发明人/申请人/日期/IPC)
  ├─ 摘要 + 权利要求 + 附图
  ├─ 专利族信息 (同族专利)
  ├─ 引用信息 (前引/后引)
  └─ 法律状态
```

### F3 — 上传专利找相似

**用户流程：**
1. 用户上传专利 PDF/DOCX/TXT 文件
2. 系统自动解析文本（摘要、权利要求、说明书）
3. 提取关键技术创新点
4. 执行语义相似度检索
5. AI 逐篇对比分析
6. 返回相似专利列表 + 差异分析

**技术实现：**

```
Step 1 — 文档解析
  ├─ PDF: PyMuPDF 提取文本 + 结构识别
  ├─ DOCX: python-docx
  └─ 图像 PDF: OCR (Tesseract/PaddleOCR 备选)

Step 2 — 信息提取 (LLM)
  ├─ 技术领域分类
  ├─ 关键创新点提取
  ├─ IPC/CPC 分类预测
  ├─ 独立权利要求解析
  └─ 生成结构化检索表示

Step 3 — 语义相似度检索
  ├─ 全文向量嵌入 → FAISS 相似度搜索
  ├─ 权利要求向量 → 独立权利要求级比对
  ├─ 创新点关键词 → Elasticsearch 精确匹配
  └─ IPC 同类 → 同分类专利补充

Step 4 — AI 深度对比 (LLM)
  ├─ 逐篇对比分析:
  │   ├─ 技术方案相似度
  │   ├─ 创新点重合度
  │   ├─ 权利要求覆盖分析
  │   └─ 差异性说明
  └─ 可视化展示:
      ├─ 相似度排序柱状图
      ├─ 技术特征雷达图
      └─ 专利引用关系图
```

---

## 六、数据库设计

### PostgreSQL 核心表

```sql
-- 专利主表
patents (
    id              SERIAL PRIMARY KEY,
    patent_number   VARCHAR(50) UNIQUE NOT NULL,
    title           TEXT NOT NULL,
    abstract        TEXT,
    claims          TEXT,
    description     TEXT,
    ipc_codes       TEXT[],
    cpc_codes       TEXT[],
    inventors       TEXT[],
    applicants      TEXT[],
    publication_date DATE,
    filing_date     DATE,
    priority_date   DATE,
    legal_status    VARCHAR(50),
    country         VARCHAR(10),
    doc_type        VARCHAR(20),
    source          VARCHAR(50),       -- 数据来源
    raw_data        JSONB,             -- 原始数据
    embedding       vector(384),       -- pgvector 扩展
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);

-- 专利引用关系
patent_citations (
    id              SERIAL PRIMARY KEY,
    citing_patent   INTEGER REFERENCES patents(id),
    cited_patent    INTEGER REFERENCES patents(id),
    citation_type   VARCHAR(20),       -- forward/backward
    UNIQUE(citing_patent, cited_patent)
);

-- 用户搜索历史
search_history (
    id              SERIAL PRIMARY KEY,
    user_id         VARCHAR(100),
    query_type      VARCHAR(20),       -- intent / patent_number / similar
    query_text      TEXT,
    query_params    JSONB,
    results_count   INTEGER,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- 上传文档记录
uploaded_documents (
    id              SERIAL PRIMARY KEY,
    user_id         VARCHAR(100),
    original_name   VARCHAR(500),
    file_path       VARCHAR(1000),
    file_type       VARCHAR(20),
    extracted_text  TEXT,
    patent_number   VARCHAR(50),       -- 如从文档中提取到
    status          VARCHAR(20),       -- pending / processed / failed
    created_at      TIMESTAMP DEFAULT NOW()
);

-- 相似度分析记录
similarity_analyses (
    id                  SERIAL PRIMARY KEY,
    upload_id           INTEGER REFERENCES uploaded_documents(id),
    target_patent_id    INTEGER REFERENCES patents(id),
    similarity_score    FLOAT,
    feature_overlap     JSONB,
    ai_analysis         TEXT,
    created_at          TIMESTAMP DEFAULT NOW()
);
```

---

## 七、API 设计

### 核心 API 端点

```
# F1: 专利意图搜索
POST   /api/search/intent
  Body: { "query": "...", "filters": { "date_range": {}, "ipc": [], "country": [] } }
  Response: SSE Stream
    event: search_plan       → 检索计划
    event: search_results    → 分批搜索结果
    event: ai_analysis       → AI 解读分析
    event: done              → 完成

# F2: 专利号精准检索
GET    /api/patent/{patent_number}
  Response: { patent_detail, family, citations, legal_status }

# F2 批量: 多个专利号比对
POST   /api/patent/batch
  Body: { "patent_numbers": ["CN110123456A", "US10123456B2"] }

# F3: 上传专利找相似
POST   /api/search/similar
  Body: multipart/form-data { file, top_k, threshold }
  Response: SSE Stream
    event: extraction        → 文本提取完成
    event: features          → 创新点提取
    event: similar_patents   → 相似专利列表
    event: comparison        → AI 逐篇对比
    event: done              → 完成

# 专利详情
GET    /api/patent/{id}/details       # 完整详情
GET    /api/patent/{id}/citations     # 引用网络
GET    /api/patent/{id}/family        # 同族专利
GET    /api/patent/{id}/images        # 附图

# AI 对话 (针对特定专利的问答)
POST   /api/chat/patent/{id}
  Body: { "message": "..." }
  Response: SSE Stream

# 搜索历史
GET    /api/history?user_id={}&type={}&page={}&limit={}
DELETE /api/history/{id}
```

---

## 八、前端页面设计

### 路由结构

```
/                        → 首页（搜索入口）
/search                  → 专利意图搜索页 (F1)
/patent/[number]          → 专利号精准检索结果页 (F2)
/upload                  → 上传专利找相似页 (F3)
/compare/[id]             → 相似度对比详情页
/patent/[id]/detail       → 专利详情页
/history                  → 搜索历史页
```

### 页面布局

```
┌──────────────────────────────────────────────┐
│  Header: Logo | 搜索框 | F1/F2/F3 切换 Tab  │
├──────────────────────────────────────────────┤
│                                              │
│  ┌─ F1 意图搜索 ─────────────────────────┐  │
│  │  大搜索框 + AI 解读开关                  │  │
│  │  高级筛选面板（日期/IPC/国家/类型）      │  │
│  │  搜索结果列表 + AI 解读侧边栏            │  │
│  └────────────────────────────────────────┘  │
│                                              │
│  ┌─ F2 精准检索 ─────────────────────────┐  │
│  │  专利号输入框（自动格式识别）            │  │
│  │  专利详情卡片（著录项/摘要/权利要求）    │  │
│  │  引用网络图 + 同族专利表                 │  │
│  └────────────────────────────────────────┘  │
│                                              │
│  ┌─ F3 上传比对 ─────────────────────────┐  │
│  │  拖拽上传区（PDF/DOCX/TXT）              │  │
│  │  上传后自动解析 → 相似度结果列表         │  │
│  │  AI 逐篇对比分析 → 可视化图表            │  │
│  └────────────────────────────────────────┘  │
│                                              │
├──────────────────────────────────────────────┤
│  AI 对话面板（可折叠，SSE 流式输出）         │
└──────────────────────────────────────────────┘
```

---

## 九、数据流

### 初始化数据流（专利数据入库）

```
EPO OPS API ────┐
USPTO API ──────┤
SerpAPI ────────┼──→ Data Ingestion Pipeline ──→ PostgreSQL
Scrapy 爬虫 ────┘                                    │
                                                     │
                    ┌─────────────────────────────────┘
                    ▼
            Text Preprocessing
                    │
                    ▼
            SentenceTransformers Embedding
                    │
                    ▼
            FAISS Index (.index 文件)
```

### 搜索数据流

```
用户输入 ──→ Query Intent Analysis (LLM)
                    │
                    ▼
          ┌─────────┴─────────┐
          ▼                   ▼
   Elasticsearch          FAISS Vector
   (关键字检索)           (语义检索)
          │                   │
          └─────────┬─────────┘
                    ▼
          RRF 融合 + 去重 + 重排序
                    │
                    ▼
          LLM 分析 & 生成回答
                    │
                    ▼
          SSE Stream → 前端渲染
```

---

## 十、开发计划（分阶段）

### 第一阶段：核心检索引擎（MVP）
- [ ] 项目脚手架搭建（FastAPI + Next.js + Docker）
- [ ] PostgreSQL 数据库建模 + Alembic 迁移
- [ ] Elasticsearch 索引创建 + 基本 CRUD
- [ ] FAISS 向量索引构建管线
- [ ] SentenceTransformers 嵌入服务
- [ ] F2：专利号精准检索 API（先对接 EPO OPS）
- [ ] F2：前端专利详情页
- [ ] 基础专利数据导入（从 EPO/Google Patents 获取样本数据）

### 第二阶段：AI 搜索能力
- [ ] LiteLLM 集成（OpenAI + Ollama 本地模型）
- [ ] F1：意图解析 + 查询扩展 Agent
- [ ] F1：混合检索（关键字 + 语义）实现
- [ ] F1：RRF 结果融合 + Cross-encoder 重排序
- [ ] F1：前端搜索页 + SSE 流式展示
- [ ] AI 对话面板（专利问答）

### 第三阶段：专利相似度比对
- [ ] F3：文件上传 + 文档解析管线
- [ ] F3：专利文本信息提取（LLM）
- [ ] F3：语义相似度检索
- [ ] F3：AI 逐篇对比分析
- [ ] F3：前端上传页 + 对比结果可视化
- [ ] 相似度分析历史记录

### 第四阶段：完善与优化
- [ ] 多数据源扩展（USPTO、CNIPA 等）
- [ ] 专利爬虫（Scrapy 定期更新）
- [ ] Redis 缓存层
- [ ] 用户认证系统
- [ ] 搜索历史 + 收藏夹
- [ ] 国际化（中文/英文）
- [ ] 专利引用网络可视化
- [ ] 性能优化 + 压力测试
- [ ] Docker 生产环境部署

---

## 十一、关键设计决策

| 决策点 | 选择 | 理由 |
|--------|------|------|
| 向量数据库 | FAISS + pgvector | FAISS 高性能近似检索，pgvector 支持与关系数据联查 |
| LLM 框架 | LiteLLM | 统一接口支持多种 LLM，可灵活切换云端/本地模型 |
| 前端框架 | Next.js + shadcn/ui | patents/Vane 验证的成熟方案，SSR 友好 |
| 搜索引擎 | Elasticsearch | 成熟稳定，BM25 算法适合专利文本检索 |
| 嵌入模型 | all-MiniLM-L6-v2 + bge-large-zh | 中英文双语覆盖 |
| 流式响应 | SSE | 比 WebSocket 轻量，适合单向推送搜索进度 |
| 文件解析 | PyMuPDF + unstructured | 覆盖主流文档格式 |
| 容器化 | Docker Compose | 一键启动全部服务（ES/Redis/PG/App/Frontend） |

---

## 十二、环境变量（.env 设计）

```bash
# LLM
LLM_PROVIDER=openai           # openai / anthropic / ollama / dashscope
LLM_MODEL=gpt-4o
OPENAI_API_KEY=sk-xxx
OPENAI_BASE_URL=              # 可选，自定义 endpoint

# Embedding
EMBEDDING_MODEL=all-MiniLM-L6-v2
EMBEDDING_DEVICE=cpu          # cpu / cuda

# Elasticsearch
ES_HOST=http://localhost:9200
ES_INDEX_NAME=patents

# PostgreSQL
DATABASE_URL=postgresql://user:pass@localhost:5432/patent_search

# Redis
REDIS_URL=redis://localhost:6379

# Patent APIs
EPO_OPS_KEY=xxx
EPO_OPS_SECRET=xxx
SERPER_API_KEY=xxx            # Google Patents via SerpAPI
USPTO_API_KEY=xxx

# File Storage
UPLOAD_DIR=./uploads
MAX_UPLOAD_SIZE=50M
```
