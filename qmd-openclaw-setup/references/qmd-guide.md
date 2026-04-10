# QMD OpenClaw 详细配置指南

## 核心问题：Collection 命名冲突

QMD 接入 OpenClaw 时最大的坑是 **collection 命名冲突**：

- 配置 `name: "memory-root-main"` → 实际生成 `memory-root-main-main`
- 原因：`scopeCollectionBase(base, agentId)` 函数对 workspace 内部的 path 自动追加 `-{agentId}` 后缀

## 三个默认 Collection 的生成逻辑

OpenClaw 在 `memory.backend = "qmd"` 且 `includeDefaultMemory: true` 时，会自动生成三个 collection：

```javascript
return [
  { path: workspaceDir, pattern: "MEMORY.md", base: "memory-root" },
  { path: workspaceDir, pattern: "memory.md", base: "memory-alt" },
  { path: memory/,    pattern: "**/*.md",  base: "memory-dir" }
]
```

当 `MEMORY.md` 和 `memory.md` 同时存在时会产生路径包含冲突。

## XDG 路径隔离

每个 agent 的 QMD 数据存放在独立目录：

```
~/.openclaw/agents/{agentId}/qmd/
├── xdg-cache/qmd/index.sqlite    # 向量索引
├── xdg-config/qmd/index.yml      # collection 配置
└── xdg-config/qmd/models/       # 嵌入模型
```

## 搜索模式选择

| 模式 | 速度 | 依赖 |
|------|------|------|
| `search` (BM25) | 最快 | 无额外模型 |
| `vsearch` (向量) | 快 | embedding 模型 |
| `query` (扩展+重排) | 慢 | 1.7B + 0.6B 模型，GPU 推荐 |

## 推荐配置

```json
{
  "memory": {
    "backend": "qmd",
    "qmd": {
      "includeDefaultMemory": false,
      "searchMode": "vsearch",
      "update": {
        "interval": "5m",
        "debounceMs": 15000,
        "onBoot": true
      }
    }
  },
  "agents": {
    "list": [{
      "id": "main",
      "memorySearch": {
        "qmd": {
          "extraCollections": [{
            "name": "memory-root-main",
            "path": "/path/to/workspace",
            "pattern": "**/*.md"
          }]
        }
      }
    }]
  }
}
```

## 模型

| 模型 | 用途 | 大小 |
|------|------|------|
| embeddinggemma-300M-Q8_0 | 向量嵌入 | 328MB |
| qwen3-reranker-0.6B | 重排 | 639MB |
| qmd-query-expansion-1.7B | 查询扩展 | 1.2GB |

模型路径：`~/.cache/qmd/models/`
