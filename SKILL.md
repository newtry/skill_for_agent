---
name: qmd-openclaw-setup
description: 一键配置 OpenClaw QMD 向量搜索。适用场景：(1) 首次配置 OpenClaw 的 QMD 后端 (2) 修复 QMD collection 冲突问题 (3) 为多 agent 配置独立的 QMD 索引 (4) 分享 QMD 配置经验给其他人。功能：自动配置 QMD backend、生成 per-agent collection、处理 scopeCollectionBase 命名冲突、设置 vsearch 模式。
---

# QMD OpenClaw 一键配置

## 快速开始

在 OpenClaw 中启用 QMD 向量搜索，执行：

```bash
bash ~/.agents/skills/qmd-openclaw-setup/scripts/setup.sh
```

或让 AI agent 执行 `scripts/setup.sh` 中的命令。

## 配置内容

1. **设置 memory backend 为 qmd**
2. **配置 searchMode 为 vsearch**（向量搜索，比 query 模式快）
3. **禁用 includeDefaultMemory**（避免三个默认 collection 冲突）
4. **为每个 agent 配置独立的 extraCollections**

## 工作流程

当用户要求配置 QMD 或修复 collection 冲突时：

1. 读取并执行 `scripts/setup.sh`
2. 重启 gateway：`openclaw gateway restart`
3. 验证状态：`qmd status`
4. 触发索引：`qmd embed -f`

## 常见问题

### Collection 名字变成 `custom-1-agentId`

原因：使用了 `extraPaths` 而非 `extraCollections`。

解决：使用 `extraCollections` 并显式指定 `name` 包含 `{agentId}`。

### Collection 名字重复 agentId（如 `memory-root-main-main`）

原因：`scopeCollectionBase` 函数会对 path 在 workspace 内部的 collection 自动追加 `-{agentId}`。

解决：
- path 放在 workspace 外部
- 或在 name 中包含 agentId，QMD 会去重

### 索引文件数量不对

检查 index.yml 中的 pattern 是否正确排除了不需要的目录。

## 参考

详细说明见 `references/qmd-guide.md`
