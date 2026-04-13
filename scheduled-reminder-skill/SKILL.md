---
name: scheduled-reminder
description: Create timed reminder or cron tasks via OpenClaw cron. Use when user wants to (1) create a one-shot reminder at a specific time, (2) create a recurring scheduled task, or (3) manage existing cron jobs. Triggers on keywords like remind, schedule, cron, 提醒, 日程, 定时任务, 每天, 每周, 每月.
---

# Scheduled Reminder Skill

Create timed reminder or cron tasks via OpenClaw's `cron` subsystem, delivered via Feishu announce.

## Workflow

### Step 1: Parse User Intent

Extract:
- **Content**: What to remind (e.g., "图书馆还书"）
- **Time**: When (supports natural language: "明天7点"、"每周一9点"、"2026-04-14 07:00"）
- **Recurrence**: one-shot vs recurring

### Step 2: Determine Schedule Type

| Input | Schedule Type | Example |
|-------|--------------|---------|
| "明天X点" / "2026-04-14 X:XX" | `at` (ISO datetime) | `--at "2026-04-14T07:00:00+08:00"` |
| "每天X点" | `cron` (daily) | `--cron "0 9 * * *"` |
| "每周一X点" | `cron` (weekly) | `--cron "0 9 * * 1"` |
| "每月1号X点" | `cron` (monthly) | `--cron "0 9 1 * *"` |

### Step 3: Build Cron Command

```bash
openclaw cron create \
  --name "<任务名称>" \
  --description "<描述>" \
  --at "<ISO时间>" \          # one-shot: --at
  # OR
  --cron "<cron expr>" \      # recurring: --cron
  --session isolated \
  --message "<提醒内容>" \
  --account default \
  --announce \
  --delete-after-run          # only for one-shot
```

### Step 4: Execute

```bash
# Example: 明天早上7点提醒去图书馆还书
openclaw cron create \
  --name "图书馆还书提醒-20260414-0700" \
  --description "提醒老大明天去图书馆还书" \
  --at "2026-04-14T07:00:00+08:00" \
  --session isolated \
  --message "📚 提醒：今天要去图书馆还书" \
  --account default \
  --announce \
  --delete-after-run
```

### Step 5: Confirm to User

Report: job ID, name, scheduled time, content, and that it will auto-delete after one-shot runs.

## Important Notes

- `--announce` makes isolated agent reply delivered to Feishu (not CLI output)
- `--delete-after-run` only for one-shot; recurring jobs omit this flag
- For recurring jobs, also report the cron expression in human-readable form
- Use `openclaw cron list` to view all jobs (or read `~/.openclaw/cron/jobs.json`)
- Job ID format: `uuid-v4`

## Cron Expression Reference

```
#      ┌────────── second (optional, 0-59)
#      │  ┌────────── minute (0-59)
#      │  │  ┌────────── hour (0-23)
#      │  │  │  ┌────────── day of month (1-31)
#      │  │  │  │  ┌────────── month (1-12)
#      │  │  │  │  │  ┌────────── day of week (0-6, Sun=0)
#      │  │  │  │  │  │
#      │  │  │  │  │  │
#  ─── ┘  ┘  ┘  ┘  ┘  └─  └─
#  *    *  *  *  *  *
```

Examples:
- `0 9 * * *` → 每天 9:00
- `0 9 * * 1` → 每周一 9:00
- `0 9 1 * *` → 每月1号 9:00
- `0 */4 * * *` → 每4小时
