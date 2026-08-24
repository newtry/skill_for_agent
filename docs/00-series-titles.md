# 从会用到会管：我用 Codex 参与真实交付的几个月

副标题：基于 ERP、业务智能体和任务自动化项目的 60 篇 AI 辅助开发实践。

> [先读总论：AI 辅助开发的本质，从代码生成到可验证交付](00-ai-assisted-development-thesis.md)

## 关于这个系列

这个系列来自我在个人工程实践中持续使用 Codex 等 AI 工具的经历。它不是一套脱离项目环境的提示词教程，也不是对某种工具的功能介绍，而是对真实开发过程的记录和复盘：如何让 AI 理解一个已有系统，如何把模糊需求转成可执行任务，如何参与方案设计、编码、测试和问题排查，以及如何通过权限、流程和人工评审控制风险。

我写这个系列，是希望和更多开发者、技术负责人及 AI 实践者交流 AI 辅助开发的真实经验。文章既会记录有效的方法，也会保留失败、返工和判断失误，因为真正影响交付质量的，往往不是 AI 能不能生成代码，而是我们能否提供足够的上下文、建立清晰的工程边界，并对结果完成可靠验证。

这个系列主要面向正在使用 Vibe Coding 的人，也面向对 AI 辅助研发感兴趣、希望进一步将它用于真实项目和团队协作的人。无论你刚开始用自然语言写代码，还是正在探索智能体、任务自动化和企业研发流程，都可以从具体案例中找到可参考的方法与边界。

我更关心的不是如何让 AI 多写一些代码，而是如何让它稳定地参与真实交付，并把个人经验沉淀成团队可以理解、复用和改进的工程方法。希望这些实践能为企业落地 AI 提供一些可验证、可执行的参考，让 AI 从个人效率工具逐步成为研发流程中的可靠协作者。

> 说明：文章中的项目名称、环境地址、账号、订单及业务数据均会匿名化处理；保留问题结构、决策过程和验证方法。

## 这个系列会写什么

整个系列按照 AI 参与工程工作的深度逐步展开：第一辑讨论怎样让 AI 真正进入日常工作，第二辑通过具体问题展示它如何参与真实项目交付，第三辑关注如何把 AI 纳入可追踪、可验证的研发流程。第四辑转向业务智能体，讨论路由、工具、数据权限、安全与评测；第五辑继续探索任务板、多工具协作和知识沉淀；第六辑对前面的方法做阶段复盘，讨论 AI 的能力边界、常见错误，以及工程师角色可能发生的变化；第七辑则来自后续项目记录，继续讨论系统演进、完成判定、并行隔离和业务结果。

这条路径也对应了企业落地 AI 时常见的几个阶段：

```text
个人尝试 -> 项目协作 -> 流程规范 -> 业务智能体 -> 自动化协作 -> 组织方法沉淀 -> 持续演进与业务闭环
```

贯穿这些阶段的不是某个工具技巧，而是三条相互连接的工程闭环：

| 主线 | 核心问题 | 对应支点 |
| --- | --- | --- |
| 交付闭环 | AI 如何从理解任务走到有证据的结果 | 上下文、边界、工具、验证 |
| 学习闭环 | 一次经验如何变成下一次可复用的能力 | 记忆、演进 |
| 价值闭环 | 技术动作如何连接用户目标和业务结果 | 业务结果 |

整个系列的核心命题可以压缩成一句话：AI 辅助开发不是让模型多生成代码，而是把工程判断转化为可执行约束，让 AI 在明确边界内完成可验证、可演进并能连接业务结果的交付。

每篇文章都会尽量围绕一个具体问题展开，包括当时的场景、AI 参与的方式、遇到的错误、人的判断、验证过程和最终形成的方法。内容不会只展示顺利完成的结果，也不会把个别项目经验直接包装成适用于所有团队的标准答案。

## 如何阅读

这个系列不要求严格按照编号阅读。刚开始接触 Vibe Coding，可以先看第一辑，建立上下文、任务描述和执行边界的基本认识；已经在真实项目中使用 AI，可以重点阅读第二辑和第三辑；正在建设企业智能体或自动化研发流程，可以从第四辑和第五辑进入；如果更关心 AI 对工程能力和程序员角色的影响，可以直接阅读第六辑；已经开始处理 Agent 协议升级、多 AI 并行开发和业务效果衡量，则可以直接进入第七辑。

阅读这些文章时，也可以把其中的方法当作检查清单，而不是固定模板。工具、模型和项目环境会持续变化，但上下文是否充分、责任是否清晰、过程是否可追踪、结果是否经过验证，仍然是 AI 参与工程交付时需要反复回答的问题。

## 第一辑：让 AI 真正参与工作

这一辑解决 AI 进入真实项目之前的基本问题：它需要知道什么、任务怎样定义、执行过程中如何保持事实连续、权限应该停在哪里，以及哪些低风险场景最适合作为起点。

五篇文章形成一条连续主线：项目认知（1）→ 任务契约（2）→ 上下文治理（3）→ 受控执行（4）→ 低风险实践（5）。前四篇建立协作条件，第 5 篇再把这些条件放进 Excel、SQL 和日志三个可核验场景中。

1. [《我不是从写代码开始的，而是从让 AI 认识项目开始的》](01-understand-the-project-first.md)
2. [《从“帮我看一下”到可执行任务：如何向 AI 描述真实需求》](02-from-vague-request-to-executable-task.md)
3. [《上下文决定结果：为什么 AI 有时像专家，有时像新人》](03-context-determines-results.md)
4. [《AI 可以操作电脑，但不代表应该直接操作》](04-ai-can-operate-but-should-not-act-directly.md)
5. [《Excel、SQL 和日志：AI 最容易立刻产生价值的三个场景》](05-excel-sql-and-logs.md)

## 第二辑：让 AI 参与真实项目交付

这一辑用故障、数据、状态和发布案例回答：当 AI 真正进入交付，它怎样从局部代码继续推演业务边界、失败恢复、重复执行和运行环境，而不把“代码能运行”误认为系统已经正确。

十篇文章形成四个连续阶段：先从故障、边界值和批量任务中发现工程问题（6-8）；再定义 ERP 的业务边界与数据语义（9-10）；随后处理支付、积分和多实例任务中的状态收敛（11-13）；最后通过数据库迁移与环境检查完成发布（14-15）。问题从一次请求开始，最终扩展到整个系统能否安全进入目标环境。

6. [《从一条错误日志到完整调用链：我是如何用 AI 排查线上问题的》](06-from-error-log-to-call-chain.md)
7. [《一个流水号溢出问题，暴露了 AI 处理边界条件的能力》](07-sequence-number-overflow.md)
8. [《批量导入为什么最能检验 AI 的工程能力》](08-batch-import-tests-ai-engineering.md)
9. [《复杂 ERP 需求不能只看代码：如何让 AI 理解业务边界》](09-understanding-erp-boundaries.md)
10. [《接口正确不等于数据正确：一次账套维度聚合问题的启示》](10-api-correct-data-wrong-ledger-dimension.md)
11. [《用 AI 辅助支付系统开发：哪些工作可以交给它，哪些不能》](11-ai-assisted-payment-development.md)
12. [《积分冻结、确认与释放：如何让 AI 理解完整的业务状态》](12-points-freeze-confirm-release.md)
13. [《从单机定时任务到多实例运行：让 AI 帮助设计幂等机制》](13-scheduled-job-multi-instance-idempotency.md)
14. [《用 AI 对比数据库结构：如何辅助发布而不盲目执行 DDL》](14-database-diff-before-release.md)
15. [《发布前的最后一公里：让 AI 检查配置、日志、JVM 和运行环境》](15-release-last-mile.md)

## 第三辑：把 AI 纳入工程流程

这一辑把个人经验变成一条可执行、可追溯、可接管的研发流程：先定义流程和规则载体，再把需求承诺连接到方案与测试，随后在真实工作区中实施、审查和验证，最后按阶段门禁判断是否完成。

九篇文章形成一条研发生命周期：流程总图（16）→ 规则与知识载体（17）→ 需求追溯（18）→ 方案评审（19）→ 风险驱动测试（20）→ 历史现场保护（21）→ 业务代码审查（22）→ 验收验证（23）→ 完成判定（24）。

16. [《从 PRD 到代码：我最终固定下来的 AI 研发流程》](16-from-prd-to-code.md)
17. [《AGENTS.md、工作流文档和 Skill，到底应该怎么分工》](17-agents-workflow-and-skills.md)
18. [《如何让需求、验收条件、测试用例和代码实现相互追溯》](18-requirements-tests-code-traceability.md)
19. [《AI 生成的技术方案如何评审：从“看起来合理”到“可以落地”》](19-reviewing-ai-technical-proposals.md)
20. [《让 AI 自己写测试：测试通过不等于风险已经被覆盖》](20-ai-writes-tests.md)
21. [《如何让 AI 接手一个存在大量历史改动的真实代码库》](21-ai-takes-over-dirty-codebase.md)
22. [《代码审查不只是找语法错误：如何让 AI 检查业务回归风险》](22-ai-code-review-business-regression.md)
23. [《AI 修改了代码以后，我是如何验证它真的完成了需求的》](23-how-to-verify-ai-changes.md)
24. [《从分析、实现到验证：如何防止 AI 在任务中途宣布完成》](24-analysis-implementation-verification-loop.md)

## 第四辑：构建可靠的业务智能体

这一辑从研发助手转向业务产品，讨论自然语言如何经过业务语义、路由、安全、权限、工具、流程、输出和评测，最终进入真实业务环境。

十篇文章形成一条 Agent 产品生命周期：先建立架构地图，再把业务语言翻译成可路由的意图，随后落实纵深安全与运行时权限；在此基础上开放受控查询和业务动作，最后用结构化输出、回放评测和上线门禁把能力交付到真实环境。

25. [《AI Agent 不能只靠提示词：路由、工具、安全和评测》](25-reliable-agent-routing-tools-security-evaluation.md)
26. [《让 AI 听懂行业黑话：服装批发业务术语库的建设实践》](26-domain-jargon-and-agent-retrieval.md)
27. [《不是所有请求都需要 ReAct：一次 Agent 路由架构的实践》](27-not-every-request-needs-react.md)
28. [《如何防止 AI 泄露思考过程、敏感数据和内部字段》](28-agent-security-and-sensitive-data.md)
29. [《租户、账套与权限：业务 Agent 必须守住的数据边界》](29-agent-tenant-ledger-permission-boundaries.md)
30. [《从自由 SQL 到受控查询：如何平衡 Agent 能力与数据安全》](30-controlled-sql-for-agent.md)
31. [《为什么业务 Agent 不能只会回答，还必须能够推动业务流程》](31-agent-must-drive-business-process.md)
32. [《从 Markdown 到业务卡片：让 Agent 输出真正可用的结果》](32-agent-cards-and-usable-output.md)
33. [《模型觉得正确还不够：如何构建可回放、可评测的 Agent》](33-agent-replayable-evaluation.md)
34. [《智能体上线前要验证什么：一次真实项目的发布检查实践》](34-agent-release-checklist.md)

## 第五辑：从个人助手到自动化协作

这一辑关注多会话、多工具和任务自动化中的协作问题：如何保存现场、隔离写入、回写证据，并让重复经验进入团队资产。

35. [《任务板接入 Codex：让 AI 从等待提问走向主动领取任务》](35-taskboard-codex-claim-task.md)
36. [《AI 自动完成任务后，为什么仍然需要“待评审”状态》](36-ai-completed-needs-review.md)
37. [《从认领、实现到回写：AI 任务自动化的完整闭环》](37-ai-task-automation-loop.md)
38. [《Codex 和 Claude Code 如何协作，而不是互相覆盖》](38-codex-claude-code-collaboration.md)
39. [《跨会话继续开发：如何解决 AI 换会话就失忆的问题》](39-cross-session-development-memory.md)
40. [《如何让多个 AI 工具共享同一套项目规则和研发记忆》](40-shared-ai-project-rules.md)
41. [《从会话记录自动生成工作日报：把 AI 使用过程变成知识资产》](41-session-records-to-work-assets.md)
42. [《从一次性对话到持续知识沉淀：文档、记忆、Skill 与任务板》](42-conversation-to-continuous-knowledge.md)
43. [《什么时候应该把提示词升级为 Skill》](43-when-prompt-becomes-skill.md)
44. [《如何把个人 AI 使用经验沉淀成团队可复用的研发流程》](44-personal-ai-practice-to-team-process.md)

## 第六辑：阶段复盘与责任边界

这一辑不是全系列终点，而是对前五辑的阶段性复盘：哪些工作适合自动化，责任怎样划分，AI 又如何改变工程能力的评价标准。

45. [《AI 最擅长做什么，最不适合替人决定什么》](45-ai-strengths-and-human-decisions.md)
46. [《为什么提示词技巧不是 AI 编程的核心竞争力》](46-prompting-is-not-core-competence.md)
47. [《真实项目中，AI 最容易犯的十类错误》](47-common-ai-engineering-mistakes.md)
48. [《不要只看 AI 写了多少代码，要看它完成了多少验证》](48-verify-more-than-code-volume.md)
49. [《如何划分 AI 的自动执行边界与人工确认边界》](49-ai-execution-and-human-confirmation-boundaries.md)
50. [《从“让 AI 写代码”到“要求 AI 为交付结果提供证据”》](50-from-code-generation-to-delivery-responsibility.md)
51. [《用了几个月 Codex 后，我对程序员角色变化的理解》](51-programmer-role-after-codex.md)
52. [《AI 没有取代工程能力，反而提高了工程能力的门槛》](52-ai-raises-engineering-bar.md)

## 第七辑：让 AI 系统持续演进

这一辑来自后续项目的新问题：第一版交付之后，协议如何退出旧链路，多个 AI 如何并行，测试和共享环境如何隔离，以及技术完成怎样连接业务效果。

其中第 53-57 篇讨论能力、协议和业务结果如何演进，第 58-60 篇讨论并行开发、测试资源和共享数据库的环境治理。

53. [《规则优先，LLM 兜底：意图识别为什么需要统一注册表》](53-rules-first-llm-fallback-intent-registry.md)
54. [《停止执行不等于任务完成：Agent 如何判断用户目标真的达成》](54-agent-completion-policy.md)
55. [《协议升级最难的不是切到 V2，而是安全删除旧链路》](55-protocol-v2-legacy-cleanup.md)
56. [《技术方案写完以后：如何用 AI 持续审计“还有哪些没有实现”》](56-ai-audits-technical-design-implementation-gap.md)
57. [《Agent 如何从任务完成走向业务结果：曝光、反馈与净成交归因》](57-agent-business-outcome-attribution.md)
58. [《AI 并行开发为什么需要 Git Worktree 和写入隔离》](58-parallel-ai-development-worktree-isolation.md)
59. [《测试为什么真的上传了 OSS：AI 开发中的环境污染与副作用隔离》](59-test-environment-pollution-and-side-effects.md)
60. [《共享开发库里的强约束：为什么上线门禁不能提前成为团队阻塞》](60-shared-development-database-release-gates.md)

## 结语

[《当 AI 进入交付系统之后，我们真正需要管理什么》](00-series-epilogue.md)重新收束三条闭环，并讨论这套方法最终把工程师推向了什么位置。
