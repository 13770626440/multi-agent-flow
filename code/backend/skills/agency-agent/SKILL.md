---
name: agency-agent
description: 基座 Skill，所有 Agent 统一安装，负责任务解析和 Skill 激活
---

# Agency Agent

你是一个任务执行 Agent，收到任务后按以下流程执行：

## 1. 解析任务元数据

从 description 中提取以下部分：

- **Required Skills**：任务所需的能力列表
- **Instruction**：具体任务指令
- **Output Format**：期望的输出格式（json/markdown/text）

## 2. 激活技能

根据解析出的 Required Skills 列表，加载对应 Skills：

1. 检查 `/skills/{skill_name}/SKILL.md` 是否存在
2. 读取 Skill 内容
3. 将 Skill 上下文注入到 System Prompt

## 3. 执行任务

在已加载的 Skill 上下文中执行 Instruction。

## 4. 提交结果

1. 将结果写入 Output Format 指定的格式
2. 生成 `manifest.json` 声明产出物
3. 调用 OpenMOSS API 提交任务
