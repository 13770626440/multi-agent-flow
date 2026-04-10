# 代码复用任务清单（从 subagent-flow 复制）

## 文档信息
- **创建日期**: 2026-04-09
- **来源**: D:\coding\subagent-flow
- **目标**: D:\coding\multi-agent-flow\code\backend
- **总任务数**: 10 个
- **单任务时长**: ≤15 分钟

---

## 任务 1: 复制 official-collaboration 执行器
**任务 ID**: REUSE-001-T01
**预计时长**: 15 分钟
**负责人**: 全栈 A

**输入**:
- 来源目录：`D:\coding\subagent-flow\main_practice\execution\official-collaboration\`
- 目标目录：`D:\coding\multi-agent-flow\code\backend\execution\`

**执行步骤**:
1. 创建目标目录：`mkdir -p code/backend/execution/official-collaboration`
2. 复制所有文件：`xcopy /E /I /Y source\* target\`
3. 验证文件完整性
4. 更新导入路径（如果需要）

**输出**:
- code/backend/execution/official-collaboration/ 目录
- 10 个文件（8 个.js, 1 个.json, 1 个.md）

**验证方法**:
```bash
ls -lh code/backend/execution/official-collaboration/
# 应该看到 main.js, collaboration-manager-with-fallback.js 等文件
```

**回滚方案**:
```bash
rm -rf code/backend/execution/official-collaboration
```

**验收标准**:
- [ ] 所有文件复制成功
- [ ] 文件完整性验证通过
- [ ] 无复制错误

---

## 任务 2: 复制 agent-mapping.js
**任务 ID**: REUSE-001-T02
**预计时长**: 10 分钟
**负责人**: 全栈 A

**输入**:
- 来源：`D:\coding\subagent-flow\skills\multi-agent-collaboration\src\agent-mapping.js`
- 目标：`D:\coding\multi-agent-flow\code\backend\utils\`

**执行步骤**:
1. 创建目标目录：`mkdir -p code/backend/utils`
2. 复制文件：`copy source target`
3. 验证文件内容

**输出**:
- code/backend/utils/agent-mapping.js 文件

**验证方法**:
```bash
cat code/backend/utils/agent-mapping.js
# 检查 taskTypeMapping 和 keywordMapping
```

**回滚方案**:
```bash
rm code/backend/utils/agent-mapping.js
```

**验收标准**:
- [ ] 文件复制成功
- [ ] 映射表完整（20+ 任务类型，15+ 关键词）

---

## 任务 3: 复制 execution-plan-manager.js
**任务 ID**: REUSE-001-T03
**预计时长**: 15 分钟
**负责人**: 全栈 A

**输入**:
- 来源：`D:\coding\subagent-flow\skills\multi-agent-collaboration\src\execution-plan-manager.js`
- 目标：`D:\coding\multi-agent-flow\code\backend\core\`

**执行步骤**:
1. 创建目标目录：`mkdir -p code/backend/core`
2. 复制文件
3. 验证依赖图构建函数
4. 验证拓扑排序函数

**输出**:
- code/backend/core/execution-plan-manager.js 文件

**验证方法**:
```bash
cat code/backend/core/execution-plan-manager.js
# 检查 buildDependencyGraph 和 topologicalSort 函数
```

**回滚方案**:
```bash
rm -rf code/backend/core
```

**验收标准**:
- [ ] 文件复制成功
- [ ] 核心算法完整

---

## 任务 4: 复制 work-order-system.js
**任务 ID**: REUSE-001-T04
**预计时长**: 15 分钟
**负责人**: 全栈 A

**输入**:
- 来源：`D:\coding\subagent-flow\skills\multi-agent-collaboration\src\work-order-system.js`
- 目标：`D:\coding\multi-agent-flow\code\backend\core\`

**执行步骤**:
1. 复制文件到 core 目录
2. 验证工单创建函数
3. 验证通知机制

**输出**:
- code/backend/core/work-order-system.js 文件

**验证方法**:
```bash
cat code/backend/core/work-order-system.js
# 检查 createPlan 和 createTask 函数
```

**回滚方案**:
```bash
rm code/backend/core/work-order-system.js
```

**验收标准**:
- [ ] 文件复制成功
- [ ] 工单系统核心功能完整

---

## 任务 5: 复制 review-manager.js
**任务 ID**: REUSE-001-T05
**预计时长**: 15 分钟
**负责人**: 全栈 A

**输入**:
- 来源：`D:\coding\subagent-flow\skills\multi-agent-collaboration\src\review-manager.js`
- 目标：`D:\coding\multi-agent-flow\code\backend\core\`

**执行步骤**:
1. 复制文件
2. 验证评审创建函数
3. 验证评审结果处理函数

**输出**:
- code/backend/core/review-manager.js 文件

**验证方法**:
```bash
cat code/backend/core/review-manager.js
# 检查 createReview 和 completeReview 函数
```

**回滚方案**:
```bash
rm code/backend/core/review-manager.js
```

**验收标准**:
- [ ] 文件复制成功
- [ ] 评审流程完整

---

## 任务 6: 复制 skill-integration-manager.js
**任务 ID**: REUSE-001-T06
**预计时长**: 15 分钟
**负责人**: 全栈 A

**输入**:
- 来源：`D:\coding\subagent-flow\main_practice\skills\skill-integration-manager.js`
- 目标：`D:\coding\multi-agent-flow\code\backend\skills\`

**执行步骤**:
1. 创建目标目录：`mkdir -p code/backend/skills`
2. 复制文件
3. 验证 Skill 编排逻辑

**输出**:
- code/backend/skills/skill-integration-manager.js 文件

**验证方法**:
```bash
cat code/backend/skills/skill-integration-manager.js
# 检查 registerSkill 和 developTestDeploy 函数
```

**回滚方案**:
```bash
rm -rf code/backend/skills
```

**验收标准**:
- [ ] 文件复制成功
- [ ] Skill 编排逻辑完整

---

## 任务 7: 复制工单模板（6 个）
**任务 ID**: REUSE-001-T07
**预计时长**: 15 分钟
**负责人**: 全栈 B

**输入**:
- 来源：`D:\coding\subagent-flow\other_practice\templates\`
- 目标：`D:\coding\multi-agent-flow\docs\templates\`

**执行步骤**:
1. 创建目标目录：`mkdir -p docs/templates`
2. 复制所有模板文件
3. 验证模板完整性

**输出**:
- docs/templates/ 目录
- 6 个模板文件（需求、开发、设计、验收、README、使用说明）

**验证方法**:
```bash
ls -lh docs/templates/
# 应该看到 6 个.md 模板文件
```

**回滚方案**:
```bash
rm -rf docs/templates
```

**验收标准**:
- [ ] 所有模板复制成功
- [ ] 模板格式正确

---

## 任务 8: 复制 Agent 定义文件
**任务 ID**: REUSE-001-T08
**预计时长**: 15 分钟
**负责人**: 全栈 B

**输入**:
- 来源：`D:\coding\subagent-flow\main_practice\profiles\`
- 目标：`D:\coding\multi-agent-flow\docs\agents\`

**执行步骤**:
1. 创建目标目录：`mkdir -p docs/agents`
2. 复制所有 Agent 定义文件
3. 验证 IDENTITY.md 文件

**输出**:
- docs/agents/ 目录
- Agent 定义文件

**验证方法**:
```bash
ls -lh docs/agents/
cat docs/agents/coordinator/IDENTITY.md
```

**回滚方案**:
```bash
rm -rf docs/agents
```

**验收标准**:
- [ ] Agent 定义文件完整
- [ ] IDENTITY.md 格式正确

---

## 任务 9: 更新导入路径
**任务 ID**: REUSE-001-T09
**预计时长**: 15 分钟
**负责人**: 全栈 A

**输入**:
- 所有复用的代码已复制

**执行步骤**:
1. 检查所有.js 文件的导入语句
2. 更新路径为新的目录结构
3. 验证无语法错误

**输出**:
- 更新后的导入路径

**验证方法**:
```bash
grep -r "require\|import" code/backend/ | head -20
```

**回滚方案**:
```bash
# 使用 git 回滚
git checkout HEAD~1 code/backend/
```

**验收标准**:
- [ ] 所有导入路径正确
- [ ] 无语法错误

---

## 任务 10: 验证复用代码
**任务 ID**: REUSE-001-T10
**预计时长**: 15 分钟
**负责人**: 全员

**输入**:
- 所有复用代码已复制
- 导入路径已更新

**执行步骤**:
1. 运行代码检查：`python -m py_compile` 或 `node --check`
2. 验证核心函数可调用
3. 记录问题清单

**输出**:
- 代码验证报告
- 问题清单（如有）

**验证方法**:
```bash
# Python 文件
python -m py_compile code/backend/services/*.py

# Node.js 文件
node --check code/backend/utils/agent-mapping.js
```

**回滚方案**:
```bash
# 标记有问题的文件
```

**验收标准**:
- [ ] 所有文件语法正确
- [ ] 核心函数可调用
- [ ] 无严重问题

---

## 复用代码汇总

| 任务 | 来源文件数 | 目标目录 | 复用率 |
|------|-----------|---------|--------|
| T01 | 10 个文件 | execution/ | 100% |
| T02 | 1 个文件 | utils/ | 100% |
| T03 | 1 个文件 | core/ | 100% |
| T04 | 1 个文件 | core/ | 80% |
| T05 | 1 个文件 | core/ | 70% |
| T06 | 1 个文件 | skills/ | 60% |
| T07 | 6 个文件 | docs/templates/ | 100% |
| T08 | 若干文件 | docs/agents/ | 100% |
| **总计** | **22+ 个文件** | | **约 1500 行代码** |

---

## 实施建议

### 优先级
1. **高优先级**（阶段一前完成）:
   - T01: official-collaboration 执行器
   - T02: agent-mapping.js
   - T07: 工单模板

2. **中优先级**（阶段一完成）:
   - T03: execution-plan-manager.js
   - T04: work-order-system.js
   - T06: skill-integration-manager.js

3. **低优先级**（阶段二完成）:
   - T05: review-manager.js
   - T08: Agent 定义文件

### 注意事项
1. **路径更新**: 所有相对路径需要更新为新项目路径
2. **依赖检查**: 检查是否有缺失的依赖库
3. **测试验证**: 每个文件复制后运行简单测试

---

*文档版本：v1.0*
*创建日期：2026-04-09*
*状态：待执行*
