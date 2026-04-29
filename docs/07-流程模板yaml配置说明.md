# 07-流程模板 YAML 配置说明

> **文档用途**：详细说明 Multi-Agent-Flow 流程模板的 YAML 配置语法、属性含义、配置流程及示例。
> **适用对象**：产品经理、架构师、Agent 配置人员
> **维护规则**：新增模板属性或语法变更时需同步更新本文档。

---

## 1. 模板文件概述

### 1.1 什么是流程模板？

流程模板是一个 YAML 文件，用于定义多 Agent 协同工作的完整流程。它包含：
- **输入参数定义**：任务启动时需要提供的参数
- **角色定义**：流程中涉及的 Agent 角色及其配置
- **任务节点**：流程中的各个步骤，包括依赖关系、执行角色、输出要求等

### 1.2 模板文件位置

```
D:\coding\multi-agent-flow\template\
├── simple-dev-flow.yaml      # 简单开发流程模板
├── test-agency-flow.yaml     # Agent 供给测试模板
└── e2e-smoke-test.yaml       # 端到端冒烟测试模板
```

### 1.3 模板加载流程

```
用户/开发者
    ↓ 创建/编辑 YAML 文件
template/ 目录
    ↓ Watchdog 监控（文件变更自动触发）
Backend TemplateLoader
    ↓ YAML 解析 → Schema 校验 → DAG 校验
Redis 缓存（template:{template_id}）
    ↓ 触发 Agent 动态供给
AgentProvisioner
    ↓ 检查并创建缺失的 Agent
OpenClaw Agent 创建完成
```

---

## 2. 完整 YAML Schema 定义

### 2.1 顶层结构

```yaml
template_id: "string"          # 模板唯一标识（必填）
version: "string"              # 模板版本号（必填）
description: "string"          # 模板描述（必填）

input_schema:                  # 输入参数定义（可选）
  param_name:
    type: "string"             # 参数类型
    required: true             # 是否必填
    default: "default_value"   # 默认值
    description: "参数说明"

roles:                         # 角色定义（可选，但强烈建议）
  role_name:
    model: "qwen3.6-plus"      # 使用的模型
    description: "角色描述"

tasks:                         # 任务节点列表（必填）
  - task_id: "string"          # 任务唯一标识
    name: "string"             # 任务名称
    type: "fixed|dynamic|review"  # 任务类型
    dependencies: []           # 依赖的任务 ID 列表
    target_role: "string"      # 执行角色
    required_skills: []        # 所需技能
    execution_context:         # 执行上下文
      instruction: "string"    # 任务指令
      input_mapping: {}        # 输入映射
      output_format: "string"  # 输出格式
    output_definition:         # 输出定义
      type: "file|json"        # 输出类型
      path: "string"           # 输出路径
    acceptance_criteria: []    # 验收标准
    control:                   # 执行控制（可选）
      timeout: 300             # 超时时间（秒）
      retry_policy:            # 重试策略
        max_retries: 2
    user_confirmation:         # 用户确认（可选）
      required: true           # 是否需要确认
      prompt: "string"         # 确认提示
      timeout: 3600            # 确认超时（秒）
```

---

## 3. 属性详细说明

### 3.1 模板元信息

| 属性 | 类型 | 必填 | 说明 | 示例 |
|:---|:---|:---:|:---|:---|
| `template_id` | string | ✅ | 模板唯一标识，只能包含字母、数字、连字符 | `"simple-dev-flow"` |
| `version` | string | ✅ | 模板版本号，建议使用语义化版本（MAJOR.MINOR.PATCH） | `"1.0.0"` |
| `description` | string | ✅ | 模板的中文描述，说明模板的用途 | `"简单开发流程模板"` |

### 3.2 input_schema（输入参数定义）

定义任务启动时需要提供的参数，支持变量替换。

| 属性 | 类型 | 必填 | 说明 | 示例 |
|:---|:---|:---:|:---|:---|
| `type` | string | ✅ | 参数类型：`string`, `number`, `boolean`, `array`, `object` | `"string"` |
| `required` | boolean | ❌ | 是否必填，默认 `false` | `true` |
| `default` | any | ❌ | 默认值，如果用户未提供则使用此值 | `"FastAPI + Vue3"` |
| `description` | string | ❌ | 参数说明，帮助用户理解 | `"技术栈"` |

**使用方式**：
在任务指令中通过 `${input.param_name}` 引用：
```yaml
instruction: "请使用 ${input.tech_stack} 技术栈开发项目"
```

### 3.3 roles（角色定义）

定义流程中涉及的 Agent 角色，**强烈建议配置**，否则系统不会自动创建 Agent。

| 属性 | 类型 | 必填 | 说明 | 示例 |
|:---|:---|:---:|:---|:---|
| `model` | string | ❌ | 使用的 LLM 模型，默认 `qwen3.6-plus` | `"qwen3.6-plus"` |
| `description` | string | ❌ | 角色职责描述 | `"产品经理，负责需求分析"` |

**角色命名规范**：
- 使用小写字母和连字符（如 `product-manager`）
- 避免使用特殊字符
- 建议与行业标准角色名称一致

**系统内置角色参考**：
| 角色 | 职责 |
|:---|:---|
| `product-manager` | 产品经理，负责需求分析和 PRD 文档 |
| `tech-lead` | 技术负责人，负责任务分解和架构设计 |
| `executor` | 执行 Agent，负责代码开发 |
| `reviewer` | 审查 Agent，负责代码审查 |
| `devops` | 运维 Agent，负责部署上线 |

### 3.4 tasks（任务节点列表）

定义流程中的各个任务节点。

#### 3.4.1 任务基本信息

| 属性 | 类型 | 必填 | 说明 | 示例 |
|:---|:---|:---:|:---|:---|
| `task_id` | string | ✅ | 任务唯一标识，只能包含字母、数字、连字符 | `"req-analysis"` |
| `name` | string | ✅ | 任务中文名称 | `"需求分析"` |
| `type` | string | ✅ | 任务类型：`fixed`（固定）/ `dynamic`（动态）/ `review`（评审） | `"fixed"` |
| `dependencies` | array | ❌ | 依赖的前置任务 ID 列表 | `["req-analysis"]` |
| `target_role` | string | ✅ | 执行此任务的 Agent 角色 | `"product-manager"` |

**任务类型说明**：

| 类型 | 说明 | 适用场景 | 子任务来源 |
|:---|:---|:---|:---|
| `fixed` | 固定任务 | 标准流程（需求分析、部署上线） | 模板预定义 |
| `dynamic` | 动态任务 | 复杂任务（任务分解、方案设计） | Agent 运行时分解 |
| `review` | 评审任务 | 质量关卡（代码审查、测试验收） | 模板预定义 |

#### 3.4.2 required_skills（所需技能）

定义执行此任务需要的 Skills，系统会自动加载对应 Skill 内容。

```yaml
required_skills:
  - "decomposer-skill"      # 任务分解技能
  - "json-validator"        # JSON 校验技能
```

**Skill 加载路径**：`/app/skills/{skill_name}/SKILL.md`

#### 3.4.3 execution_context（执行上下文）

| 属性 | 类型 | 必填 | 说明 | 示例 |
|:---|:---|:---:|:---|:---|
| `instruction` | string | ✅ | 任务指令，支持变量替换 | `"请分析需求..."` |
| `input_mapping` | object | ❌ | 输入参数映射，将前置任务输出映射到变量 | `{"doc": "${req-analysis.output}"}` |
| `output_format` | string | ❌ | 期望的输出格式：`markdown`, `json`, `text` | `"markdown"` |

**变量替换语法**：
- `${input.param_name}`：引用输入参数
- `${task_id.output}`：引用前置任务的输出
- `${task_id.output_path}`：引用前置任务的输出文件路径

**instruction 编写建议**：
1. 使用清晰的步骤说明
2. 明确输出要求
3. 指定文件保存路径
4. 提供示例格式

#### 3.4.4 output_definition（输出定义）

| 属性 | 类型 | 必填 | 说明 | 示例 |
|:---|:---|:---:|:---|:---|
| `type` | string | ✅ | 输出类型：`file`（文件）/ `json`（JSON 数据） | `"file"` |
| `path` | string | ✅ | 输出文件路径，**必须使用 `/workspace/{task_id}/` 前缀** | `"/workspace/{task_id}/req-analysis/prd.md"` |
| `format` | string | ❌ | 文件格式（当 type=file 时） | `"markdown"` |
| `schema` | object | ❌ | JSON Schema（当 type=json 时） | 见下方示例 |

**⚠️ 路径规范**：
- ✅ 正确：`/workspace/{task_id}/req-analysis/prd.md`
- ❌ 错误：`/home/node/.openclaw/workspace/req-analysis/prd.md`
- ❌ 错误：`/workspace/req-analysis/prd.md`（缺少 `{task_id}`）

#### 3.4.5 acceptance_criteria（验收标准）

定义任务完成的验收标准，用于评审任务验证。

```yaml
acceptance_criteria:
  - "输出完整的 PRD 文档"
  - "包含至少 3 个核心功能"
  - "包含非功能性需求说明"
```

#### 3.4.6 control（执行控制）

| 属性 | 类型 | 必填 | 说明 | 示例 |
|:---|:---|:---:|:---|:---|
| `timeout` | int | ❌ | 任务超时时间（秒），默认 300 | `600` |
| `retry_policy.max_retries` | int | ❌ | 最大重试次数，默认 2 | `3` |

#### 3.4.7 user_confirmation（用户确认）

任务完成后是否需要用户确认才能继续。

| 属性 | 类型 | 必填 | 说明 | 示例 |
|:---|:---|:---:|:---|:---|
| `required` | boolean | ❌ | 是否需要用户确认，默认 `false` | `true` |
| `prompt` | string | ❌ | 确认提示信息 | `"需求分析已完成，是否继续？"` |
| `timeout` | int | ❌ | 确认超时时间（秒），默认 3600 | `7200` |

---

## 4. 配置流程

### 4.1 人员配置流程（产品经理/架构师）

#### 步骤 1：确定流程需求
- 明确流程目标（如：开发流程、测试流程）
- 识别流程中的各个步骤
- 确定步骤之间的依赖关系

#### 步骤 2：定义角色
- 列出流程中涉及的 Agent 角色
- 为每个角色编写职责描述
- 选择合适的 LLM 模型

#### 步骤 3：编写任务节点
- 为每个步骤定义任务节点
- 编写清晰的任务指令
- 设置依赖关系
- 定义输出格式和路径

#### 步骤 4：配置验收标准
- 为每个任务定义验收标准
- 确保标准可量化、可验证

#### 步骤 5：保存并验证
- 将 YAML 文件保存到 `template/` 目录
- 检查 Backend 日志确认加载成功
- 验证 Redis 缓存是否写入

### 4.2 Agent 配置流程（自动）

#### 步骤 1：模板加载触发
```
用户保存 YAML 文件到 template/ 目录
    ↓
Watchdog 检测到文件变更
    ↓
TemplateLoader.load_template() 被调用
```

#### 步骤 2：模板校验
```
1. YAML 语法解析
2. Schema 校验（必填字段、类型检查）
3. DAG 校验（循环依赖检测、依赖存在性检查）
```

#### 步骤 3：缓存写入
```
Redis SET template:{template_id} {template_data}
    ↓
本地缓存更新
```

#### 步骤 4：Agent 动态供给
```
读取 roles 字段
    ↓
对每个角色调用 AgentProvisioner.ensure_role_exists()
    ↓
检查 OpenClaw 中是否已存在该 Agent
    ├─ 存在 → 发送入职包更新
    └─ 不存在 → 创建 Agent → 发送入职包 → 配置 Cron
```

#### 步骤 5：Agent 入职
```
Agent 收到入职包
    ↓
保存 AGENTS.md（包含角色定义、Skills、Workspace 规范）
    ↓
调用 OpenMOSS API 注册自己
    ↓
获取 API Key
    ↓
准备就绪，等待任务派发
```

---

## 5. 完整示例

### 5.1 示例 1：简单开发流程（simple-dev-flow.yaml）

**适用场景**：标准的软件开发流程，包含需求分析、任务分解、代码审查、部署上线。

```yaml
# 模板元信息
template_id: "simple-dev-flow"
version: "1.0.0"
description: "简单开发流程模板（含固定、动态、评审节点，支持用户确认）"

# 输入参数定义
input_schema:
  project_name:
    type: string
    required: true
    description: "项目名称"
  tech_stack:
    type: string
    default: "FastAPI + Vue3 + PostgreSQL"
    description: "技术栈"

# 角色定义
roles:
  product-manager:
    model: "qwen3.6-plus"
    description: "产品经理，负责需求分析"
  tech-lead:
    model: "qwen3.6-plus"
    description: "技术负责人，负责任务分解"
  reviewer:
    model: "qwen3.6-plus"
    description: "审查 Agent，负责代码审查"
  devops:
    model: "qwen3.6-plus"
    description: "运维 Agent，负责部署上线"

# 任务节点
tasks:
  # 节点 1：需求分析（固定任务）
  - task_id: "req-analysis"
    name: "需求分析"
    type: fixed
    dependencies: []
    target_role: "product-manager"
    
    execution_context:
      instruction: |
        请分析"${input.project_name}"的需求，输出需求文档。
        
        包含：
        1. 核心功能列表
        2. 非功能性需求（性能、安全性）
        3. 技术栈建议：${input.tech_stack}
        
        **存储路径**: 请将文档保存至 `/workspace/{task_id}/req-analysis/prd.md`
      output_format: "markdown"
    
    output_definition:
      type: "file"
      path: "/workspace/{task_id}/req-analysis/prd.md"
    
    acceptance_criteria:
      - "输出完整的 PRD 文档"
      - "包含至少 3 个核心功能"
    
    user_confirmation:
      required: true
      prompt: "需求分析已完成，请确认是否继续？"
      timeout: 3600

  # 节点 2：开发任务分解（动态任务）
  - task_id: "dev-breakdown"
    name: "开发任务分解"
    type: dynamic
    dependencies: ["req-analysis"]
    target_role: "tech-lead"
    required_skills: ["decomposer-skill", "json-validator"]
    
    execution_context:
      instruction: |
        请根据需求文档（${req-analysis.output}），将"${input.project_name}"的开发任务分解为具体的子任务。
        
        技术栈：${input.tech_stack}
        
        要求：
        1. 每个子任务必须是原子性的（可在 2-4 小时内完成）
        2. 明确子任务之间的依赖关系
        3. 为每个子任务分配角色（backend/frontend/database）
        4. 输出合法的 JSON 数组
      
      input_mapping:
        requirement_doc: "${req-analysis.output}"
        tech_stack: "${input.tech_stack}"
      
      output_format: "json"
    
    output_definition:
      type: "json"
      path: "/workspace/{task_id}/dev-breakdown/sub-tasks.json"
      schema:
        type: array
        items:
          type: object
          properties:
            name: {type: string}
            role: {type: string, enum: ["backend", "frontend", "database"]}
            instruction: {type: string}
            dependencies: {type: array, items: {type: string}}
          required: ["name", "role", "instruction"]
    
    user_confirmation:
      required: true
      prompt: "任务分解已完成，请确认分解结果是否合理？"
      timeout: 3600

  # 节点 3：代码审查（评审任务）
  - task_id: "code-review"
    name: "代码审查"
    type: review
    dependencies: ["dev-breakdown"]
    target_role: "reviewer"
    
    execution_context:
      instruction: |
        请审查开发任务的产出物。
        
        审查标准：
        1. 代码质量（命名规范、注释、错误处理）
        2. 功能完整性（是否满足验收标准）
        3. 安全性（SQL 注入、XSS 防护）
      input_mapping:
        codebase: "${dev-breakdown.output}"
      output_format: "markdown"
    
    output_definition:
      type: "file"
      path: "/workspace/{task_id}/code-review/review-report.md"
    
    acceptance_criteria:
      - "所有代码通过静态检查"
      - "无 P0/P1 级别安全漏洞"
      - "单元测试覆盖率 > 80%"
    
    user_confirmation:
      required: true
      prompt: "代码审查已完成，请确认审查结果？"
      timeout: 3600

  # 节点 4：部署上线（固定任务）
  - task_id: "deploy"
    name: "部署上线"
    type: fixed
    dependencies: ["code-review"]
    target_role: "devops"
    
    execution_context:
      instruction: |
        请将项目部署到生产环境。
        
        部署步骤：
        1. 构建 Docker 镜像
        2. 运行数据库迁移
        3. 部署到 Kubernetes 集群
        4. 验证健康检查
      input_mapping:
        codebase: "${code-review.output}"
      output_format: "markdown"
    
    output_definition:
      type: "file"
      path: "/workspace/{task_id}/deploy/deploy-log.md"
    
    acceptance_criteria:
      - "部署成功，健康检查通过"
      - "无错误日志"
    
    user_confirmation:
      required: true
      prompt: "部署已完成，请确认服务是否正常运行？"
      timeout: 3600
```

**流程图**：
```
需求分析 → 任务分解 → 代码审查 → 部署上线
   ↓          ↓          ↓          ↓
 用户确认   用户确认   用户确认   用户确认
```

---

### 5.2 示例 2：数据分析师流程（data-analysis-flow.yaml）

**适用场景**：数据分析任务，包含数据收集、数据清洗、分析报告生成。

```yaml
template_id: "data-analysis-flow"
version: "1.0.0"
description: "数据分析流程模板（数据收集 → 清洗 → 分析 → 报告）"

input_schema:
  dataset_name:
    type: string
    required: true
    description: "数据集名称"
  data_source:
    type: string
    required: true
    description: "数据源（数据库/API/文件）"
  analysis_goal:
    type: string
    required: true
    description: "分析目标"

roles:
  data-engineer:
    model: "qwen3.6-plus"
    description: "数据工程师，负责数据收集和清洗"
  data-analyst:
    model: "qwen3.6-plus"
    description: "数据分析师，负责数据分析和报告"
  reviewer:
    model: "qwen3.6-plus"
    description: "审查 Agent，负责报告审查"

tasks:
  - task_id: "data-collection"
    name: "数据收集"
    type: fixed
    dependencies: []
    target_role: "data-engineer"
    
    execution_context:
      instruction: |
        请从 ${input.data_source} 收集 "${input.dataset_name}" 数据集。
        
        要求：
        1. 记录数据来源和采集时间
        2. 保存原始数据到 `/workspace/{task_id}/data-collection/raw_data.csv`
        3. 记录数据量（行数、列数）
      output_format: "markdown"
    
    output_definition:
      type: "file"
      path: "/workspace/{task_id}/data-collection/collection-report.md"
    
    acceptance_criteria:
      - "原始数据文件存在"
      - "数据量 > 0"
      - "记录数据来源信息"

  - task_id: "data-cleaning"
    name: "数据清洗"
    type: fixed
    dependencies: ["data-collection"]
    target_role: "data-engineer"
    
    execution_context:
      instruction: |
        请清洗原始数据（${data-collection.output}）。
        
        清洗步骤：
        1. 处理缺失值（填充或删除）
        2. 处理异常值
        3. 数据类型转换
        4. 保存清洗后的数据到 `/workspace/{task_id}/data-cleaning/clean_data.csv`
      input_mapping:
        raw_data: "${data-collection.output}"
      output_format: "markdown"
    
    output_definition:
      type: "file"
      path: "/workspace/{task_id}/data-cleaning/cleaning-report.md"
    
    acceptance_criteria:
      - "无缺失值"
      - "无异常值"
      - "数据类型正确"

  - task_id: "data-analysis"
    name: "数据分析"
    type: fixed
    dependencies: ["data-cleaning"]
    target_role: "data-analyst"
    
    execution_context:
      instruction: |
        请分析清洗后的数据（${data-cleaning.output}），回答以下问题：
        
        分析目标：${input.analysis_goal}
        
        要求：
        1. 描述性统计分析
        2. 趋势分析
        3. 关键发现
        4. 可视化图表（如适用）
      input_mapping:
        clean_data: "${data-cleaning.output}"
      output_format: "markdown"
    
    output_definition:
      type: "file"
      path: "/workspace/{task_id}/data-analysis/analysis-report.md"
    
    acceptance_criteria:
      - "包含描述性统计"
      - "包含关键发现"
      - "结论清晰"

  - task_id: "report-review"
    name: "报告审查"
    type: review
    dependencies: ["data-analysis"]
    target_role: "reviewer"
    
    execution_context:
      instruction: |
        请审查数据分析报告（${data-analysis.output}）。
        
        审查标准：
        1. 分析方法是否合理
        2. 结论是否有数据支撑
        3. 报告结构是否清晰
      output_format: "markdown"
    
    output_definition:
      type: "file"
      path: "/workspace/{task_id}/report-review/review-report.md"
    
    acceptance_criteria:
      - "方法合理"
      - "结论有数据支撑"
      - "无重大错误"
```

---

### 5.3 示例 3：内容创作流程（content-creation-flow.yaml）

**适用场景**：内容创作任务，包含选题、大纲、初稿、编辑、发布。

```yaml
template_id: "content-creation-flow"
version: "1.0.0"
description: "内容创作流程模板（选题 → 大纲 → 初稿 → 编辑 → 发布）"

input_schema:
  topic:
    type: string
    required: true
    description: "文章主题"
  target_audience:
    type: string
    required: true
    description: "目标读者"
  word_count:
    type: number
    default: 2000
    description: "目标字数"

roles:
  content-planner:
    model: "qwen3.6-plus"
    description: "内容策划，负责选题和大纲"
  writer:
    model: "qwen3.6-plus"
    description: "作者，负责撰写初稿"
  editor:
    model: "qwen3.6-plus"
    description: "编辑，负责审校和修改"
  publisher:
    model: "qwen3.6-plus"
    description: "发布 Agent，负责发布和推广"

tasks:
  - task_id: "topic-research"
    name: "选题调研"
    type: fixed
    dependencies: []
    target_role: "content-planner"
    
    execution_context:
      instruction: |
        请针对"${input.topic}"主题进行选题调研。
        
        目标读者：${input.target_audience}
        
        输出：
        1. 选题价值分析
        2. 竞品分析（同类文章）
        3. 差异化建议
      output_format: "markdown"
    
    output_definition:
      type: "file"
      path: "/workspace/{task_id}/topic-research/research-report.md"
    
    acceptance_criteria:
      - "包含选题价值分析"
      - "包含至少 3 篇竞品分析"
      - "有明确的差异化建议"

  - task_id: "outline-creation"
    name: "大纲创作"
    type: fixed
    dependencies: ["topic-research"]
    target_role: "content-planner"
    
    execution_context:
      instruction: |
        请根据选题调研报告（${topic-research.output}），创建文章大纲。
        
        目标字数：${input.word_count} 字
        
        大纲要求：
        1. 包含引言、正文、结论
        2. 每个章节有明确的要点
        3. 标注预计字数分配
      output_format: "markdown"
    
    output_definition:
      type: "file"
      path: "/workspace/{task_id}/outline-creation/article-outline.md"
    
    acceptance_criteria:
      - "结构完整"
      - "章节要点明确"
      - "字数分配合理"

  - task_id: "first-draft"
    name: "初稿撰写"
    type: fixed
    dependencies: ["outline-creation"]
    target_role: "writer"
    
    execution_context:
      instruction: |
        请根据文章大纲（${outline-creation.output}），撰写初稿。
        
        要求：
        1. 语言流畅、通俗易懂
        2. 包含具体案例
        3. 字数接近 ${input.word_count} 字
      input_mapping:
        outline: "${outline-creation.output}"
      output_format: "markdown"
    
    output_definition:
      type: "file"
      path: "/workspace/{task_id}/first-draft/article-draft.md"
    
    acceptance_criteria:
      - "字数 > ${input.word_count} * 0.8"
      - "包含至少 2 个案例"
      - "语言流畅"

  - task_id: "editing"
    name: "编辑审校"
    type: review
    dependencies: ["first-draft"]
    target_role: "editor"
    
    execution_context:
      instruction: |
        请审校初稿（${first-draft.output}）。
        
        审校标准：
        1. 语法和拼写错误
        2. 逻辑连贯性
        3. 内容准确性
        4. 可读性
        
        请直接修改文章，并输出最终版本。
      output_format: "markdown"
    
    output_definition:
      type: "file"
      path: "/workspace/{task_id}/editing/final-article.md"
    
    acceptance_criteria:
      - "无语法错误"
      - "逻辑连贯"
      - "内容准确"

  - task_id: "publishing"
    name: "发布推广"
    type: fixed
    dependencies: ["editing"]
    target_role: "publisher"
    
    execution_context:
      instruction: |
        请将最终文章（${editing.output}）发布到指定平台。
        
        发布步骤：
        1. 生成 SEO 标题和描述
        2. 添加标签和分类
        3. 生成分享文案
        4. 记录发布链接
      output_format: "markdown"
    
    output_definition:
      type: "file"
      path: "/workspace/{task_id}/publishing/publish-report.md"
    
    acceptance_criteria:
      - "包含 SEO 标题和描述"
      - "包含发布链接"
      - "包含分享文案"
```

---

### 5.4 示例 4：最小化测试模板（minimal-test-flow.yaml）

**适用场景**：快速测试模板加载和 Agent 创建流程。

```yaml
template_id: "minimal-test-flow"
version: "1.0.0"
description: "最小化测试模板（仅 1 个任务节点）"

roles:
  test-executor:
    model: "qwen3.6-plus"
    description: "测试执行 Agent"

tasks:
  - task_id: "test-task"
    name: "测试任务"
    type: fixed
    dependencies: []
    target_role: "test-executor"
    
    execution_context:
      instruction: |
        请执行测试任务，输出一条测试消息。
        
        要求：
        1. 输出"Hello, Multi-Agent-Flow!"
        2. 保存到 `/workspace/{task_id}/test-task/output.txt`
      output_format: "text"
    
    output_definition:
      type: "file"
      path: "/workspace/{task_id}/test-task/output.txt"
    
    acceptance_criteria:
      - "输出文件存在"
      - "包含测试消息"
```

---

## 6. 常见问题（FAQ）

### Q1: 模板保存后多久生效？
**A**: 通常 1-3 秒内生效。Watchdog 会监控 `template/` 目录，文件变更后自动触发加载。

### Q2: 如何确认模板加载成功？
**A**: 查看 Backend 日志：
```bash
docker logs maf-backend --tail 20
```
应包含：`Template {template_id} v{version} loaded successfully`

### Q3: 如何查看已加载的模板？
**A**: 调用 API：
```bash
curl http://localhost:8000/api/v1/templates/
```

### Q4: roles 字段可以不写吗？
**A**: 可以不写，但**强烈建议配置**。如果不配置 roles，系统不会自动创建 Agent，需要手动创建。

### Q5: 如何修改已加载的模板？
**A**: 直接编辑 `template/` 目录下的 YAML 文件，保存后自动重新加载。建议同时更新 `version` 字段。

### Q6: 如何删除模板？
**A**: 从 `template/` 目录删除 YAML 文件，Watchdog 会自动触发删除。Redis 缓存也会被清理。

### Q7: output_definition.path 为什么必须使用 `/workspace/{task_id}/`？
**A**: 这是系统规范，确保：
1. 不同任务的产出物相互隔离
2. 文件路径可预测，便于后续任务引用
3. 避免文件冲突和覆盖

### Q8: 如何调试模板？
**A**: 
1. 使用 YAML 验证工具检查语法
2. 查看 Backend 日志确认加载成功
3. 调用 API 查看模板详情
4. 创建任务实例验证流程

---

## 7. 最佳实践

### 7.1 模板设计原则

1. **单一职责**：每个模板只解决一个特定流程
2. **可复用性**：使用变量替换，避免硬编码
3. **清晰命名**：task_id 使用英文，name 使用中文
4. **完整文档**：description 详细说明模板用途
5. **版本管理**：每次修改更新 version 字段

### 7.2 任务指令编写建议

1. **明确目标**：清晰说明任务要做什么
2. **分步说明**：使用编号列表，步骤清晰
3. **指定路径**：明确文件保存路径
4. **提供示例**：给出输出格式示例
5. **设置标准**：定义验收标准

### 7.3 依赖关系设计

1. **线性流程**：简单流程使用线性依赖（A→B→C）
2. **并行任务**：复杂流程可使用并行任务（A→B,C→D）
3. **避免循环**：DAG 不允许循环依赖
4. **最小依赖**：只依赖必要的前置任务

---

*文档版本：1.0.0*
*最后更新：2026-04-28*
*维护人：架构组*
