#!/bin/bash
# OpenClaw QMD 一键配置脚本
# 用法: bash ~/.agents/skills/qmd-openclaw-setup/scripts/setup.sh

CONFIG_FILE="${OPENCLAW_CONFIG:-$HOME/.openclaw/openclaw.json}"
BACKUP_FILE=""

# ========== 回滚函数 ==========
rollback() {
    if [ -n "$BACKUP_FILE" ] && [ -f "$BACKUP_FILE" ]; then
        echo ""
        echo "⚠️ 配置失败，正在回滚..."
        cp "$BACKUP_FILE" "$CONFIG_FILE"
        echo "✅ 已回滚到备份: $BACKUP_FILE"
    fi
    exit 1
}

# 设置 trap，脚本异常退出时自动回滚
trap rollback ERR INT TERM

echo "🔧 OpenClaw QMD 配置开始..."

# ========== 第一步：检测并安装 QMD ==========
echo ""
echo "📦 检测 QMD 安装状态..."

QMD_PATH=""
for path in ~/.local/bin/qmd ~/.npm-global/bin/qmd /usr/local/bin/qmd; do
    if [ -f "$path" ]; then
        QMD_PATH="$path"
        break
    fi
done

if [ -z "$QMD_PATH" ]; then
    if command -v qmd &>/dev/null; then
        QMD_PATH=$(command -v qmd)
    fi
fi

if [ -z "$QMD_PATH" ]; then
    echo "❌ QMD 未安装，正在安装..."
    
    if command -v npm &>/dev/null; then
        echo "📦 使用 npm 安装 qmd..."
        npm install -g qmd --prefix ~/.npm-global 2>/dev/null || \
        npm install -g qmd 2>/dev/null || {
            echo "❌ npm 安装失败，请先安装 Node.js: https://nodejs.org/"
            exit 1
        }
        
        export PATH="$HOME/.npm-global/bin:$PATH"
        if command -v qmd &>/dev/null; then
            QMD_PATH=$(command -v qmd)
            echo "✅ QMD 安装成功: $QMD_PATH"
        fi
    else
        echo "❌ 未找到 npm，请先安装 Node.js: https://nodejs.org/"
        exit 1
    fi
else
    echo "✅ QMD 已安装: $QMD_PATH"
fi

# ========== 第二步：备份配置 ==========
echo ""
echo "💾 备份原配置..."
BACKUP_FILE="${CONFIG_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
cp "$CONFIG_FILE" "$BACKUP_FILE"
echo "✅ 已备份到: $BACKUP_FILE"

# ========== 第三步：更新 OpenClaw 配置 ==========
echo ""
echo "⚙️ 更新 OpenClaw 配置..."

python3 << 'PYEOF'
import json
import sys
import os

config_file = os.environ.get('OPENCLAW_CONFIG', os.path.expanduser('~/.openclaw/openclaw.json'))

with open(config_file, 'r') as f:
    config = json.load(f)

workspace = config.get('agents', {}).get('list', [{}])[0].get('workspace')
if not workspace:
    workspace = os.path.expanduser('~/.openclaw/workspace')

agents_list = config.get('agents', {}).get('list', [])

if not agents_list:
    print("📋 未检测到 agents.list，使用 memory.paths 配置")
    config['memory'] = {
        "backend": "qmd",
        "qmd": {
            "includeDefaultMemory": False,
            "searchMode": "vsearch",
            "paths": [
                {
                    "name": "memory-root-main",
                    "path": workspace,
                    "pattern": "**/*.md"
                }
            ],
            "update": {
                "interval": "5m",
                "debounceMs": 15000,
                "onBoot": True,
                "waitForBootSync": False
            }
        }
    }
    print("✅ 已添加到 memory.qmd.paths")
else:
    print(f"📋 检测到 {len(agents_list)} 个 agent，使用 per-agent extraCollections")
    config['memory'] = {
        "backend": "qmd",
        "qmd": {
            "includeDefaultMemory": False,
            "searchMode": "vsearch",
            "update": {
                "interval": "5m",
                "debounceMs": 15000,
                "onBoot": True,
                "waitForBootSync": False
            }
        }
    }

    for agent in agents_list:
        agent_id = agent.get('id', '')
        agent_workspace = agent.get('workspace', '') or workspace
        
        if not agent_id:
            continue
        
        agent['memorySearch'] = {
            'qmd': {
                'extraCollections': [
                    {
                        'name': f'memory-root-{agent_id}',
                        'path': agent_workspace,
                        'pattern': '**/*.md'
                    }
                ]
            }
        }
    print(f"✅ 已为 {len(agents_list)} 个 agent 配置 extraCollections")

with open(config_file, 'w') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

print("✅ 配置已保存")
PYEOF

# ========== 第四步：重启 Gateway ==========
echo ""
echo "🔄 重启 Gateway..."
openclaw gateway restart 2>/dev/null || echo "⚠️ 请手动运行: openclaw gateway restart"

# 成功，取消 trap
trap - ERR INT TERM

echo ""
echo "========================================"
echo "✅ 配置完成！"
echo "========================================"
echo ""
echo "验证命令（main agent）:"
echo "  cd ~/.openclaw/agents/main"
echo "  XDG_CACHE_HOME=~/.openclaw/agents/main/qmd/xdg-cache \\"
echo "  XDG_CONFIG_HOME=~/.openclaw/agents/main/qmd/xdg-config \\"
echo "  qmd status"
echo ""
echo "触发索引（main agent）:"
echo "  cd ~/.openclaw/agents/main"
echo "  XDG_CACHE_HOME=~/.openclaw/agents/main/qmd/xdg-cache \\"
echo "  XDG_CONFIG_HOME=~/.openclaw/agents/main/qmd/xdg-config \\"
echo "  qmd embed -f"
echo ""
echo "查看备份:"
echo "  ls ${CONFIG_FILE}.backup.*"
