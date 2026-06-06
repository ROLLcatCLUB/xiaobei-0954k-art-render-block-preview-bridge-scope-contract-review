# 071A Workbench Backend Preview ViewModel Contract Audit

## 目标

071A 设计一个只读的 `Workbench Preview ViewModel v0.1`，作为后续前端稳定渲染小备工作台的统一预览契约。

这个 ViewModel 面向：

- 左侧聊天区
- 右侧文档区
- 候选块
- Verifier 状态
- Agent Run Trace 预览
- 安全闸门
- 禁用按钮状态
- 审计回执

本轮只新增契约说明、样例 payload、校验脚本和审核包，不新增 endpoint，不接真实 runtime。

## 和 070 前端会话的边界

070A / 070B / 070C / 070D 是前端视觉会话，范围包括 `frontend/workbench/index.html`、CSS、左侧气泡、右侧文档块和页面视觉复测。

071A 是后端契约会话，不修改前端页面、CSS、布局 JS，也不调整前端视觉壳。071A 的产物只描述“后端未来可以给前端什么稳定结构”，不要求前端现在消费它。

## ViewModel 顶层结构

```json
{
  "viewmodel_version": "workbench_preview_viewmodel_071A_v0.1",
  "mode": "dry_run",
  "source": {},
  "gates": {},
  "left_chat": {},
  "right_workspace": {},
  "candidate_blocks": [],
  "verifier": {},
  "trace": {},
  "actions": {},
  "audit": {}
}
```

## 字段说明

| 字段 | 说明 |
| --- | --- |
| `viewmodel_version` | 固定为 `workbench_preview_viewmodel_071A_v0.1`，用于后续兼容判断。 |
| `mode` | 固定为 `dry_run`，071A 不提供真实执行态。 |
| `source` | 描述来源，不绑定真实 Agent session。`contract_id`、`assignment_id`、`runtime_session_id` 可以为空。 |
| `gates` | 所有危险能力的统一闸门。危险项必须默认 `false`，`teacher_review_required` 必须为 `true`。 |
| `left_chat.messages` | 给左侧聊天区的只读消息数组，可包含老师、小备、系统提示，但不能触发自动执行。 |
| `right_workspace.doc_sections` | 给右侧文档区的只读文档块数组。 |
| `candidate_blocks` | 候选块数组，只表达候选内容、状态和确认要求。 |
| `verifier` | 自检器状态，允许 `pending_review`、`blocked`、`needs_revision` 等预览态。 |
| `trace.events` | Agent Run Trace 的预览事件，不代表真实 streaming。 |
| `actions` | 前端按钮建议，分为 `primary`、`secondary`、`disabled`，禁用项应说明原因。 |
| `audit` | 审计回执，记录危险 true flag 收口、缺失契约、归一化说明。 |

## 071B0 消息内容格式边界

071B0 对 071A 契约补充消息内容格式边界：后端只输出原始内容和格式声明，不做 Markdown 渲染，不返回 HTML。

后端允许输出：

```text
role
speaker
content_format
content
render_policy
source
gates
audit
```

后端不得输出：

```text
content_format=html
unsafe_html
raw_html
rendered_html
innerHTML
html_allowed=true
```

`content_format` 只允许：

```text
plain_text
safe_markdown
structured_json
```

老师消息必须使用：

```text
role=teacher
content_format=plain_text
```

小备 / assistant 消息可以使用：

```text
role=assistant
content_format=safe_markdown
```

或在不需要 Markdown 时使用 `plain_text`。系统消息默认使用 `plain_text`。

所有含 `content` 的对象都必须声明：

```json
{
  "render_policy": {
    "html_allowed": false,
    "frontend_render_required": true,
    "sanitize_required": true
  }
}
```

这条边界同样适用于：

- `left_chat.messages`
- `right_workspace.doc_sections`
- `candidate_blocks`

前端后续 `070E` 可以根据 `content_format` 选择 Markdown 解析、安全 HTML 清洗和显示策略。071B0 不提供 renderer，不引入 markdown-it，不拼接 HTML。

## 危险 Gate 收口策略

071A 统一把以下危险能力收口为 `false`：

```text
can_score=false
formal_scoring_allowed=false
formal_writeback_allowed=false
feishu_write_allowed=false
kb_ingest_allowed=false
frontend_connect_allowed=false
runtime_streaming_allowed=false
export_allowed=false
```

如果上游原始输入曾出现危险 true 值，071A payload 不保留可执行 true 布尔值，只在：

```text
audit.unsafe_true_flags
audit.normalization_notes
verifier.blocking_reasons
```

中记录“曾出现、已收口、已阻断”。这样前端可以展示风险原因，但不能误把 payload 当成可执行授权。

## 三个样例 Payload

### sample_safe_payload.json

安全预览样例：

- 所有危险 gate 为 `false`。
- `teacher_review_required=true`。
- `verifier.status=pending_review`。
- 含左侧聊天、右侧文档区、候选块和 trace 预览。
- 不包含正式评分、正式导出、正式写回状态。

### sample_blocked_payload.json

危险输入被收口样例：

- `gates` 中危险字段最终全部为 `false`。
- `verifier.status=blocked`。
- `audit.unsafe_true_flags` 记录原始危险字段名。
- `audit.normalization_notes` 说明已收口。
- 不保留任何可执行危险 true 布尔值。

### sample_missing_contract_payload.json

缺少契约来源样例：

- `contract_id=null`。
- `assignment_id=null`。
- `runtime_session_id=null`。
- `verifier.status=blocked`。
- `blocking_reasons` 说明缺少 contract。
- 不自动补成可执行状态。
- `export_allowed=false`、`frontend_connect_allowed=false`。

## 校验脚本

运行：

```text
python scripts/validate_workbench_preview_viewmodel_071A.py
```

脚本校验：

- 三个 JSON 样例可解析。
- `viewmodel_version` 存在。
- `mode` 固定为 `dry_run`。
- `gates` 完整存在。
- 所有危险 gate 不得为 `true`。
- ZIP entry path 会统一归一化为 `/` 后再比对。
- `content_format` 只能是 `plain_text`、`safe_markdown`、`structured_json`。
- 禁止 `content_format=html`、`rendered_html`、`innerHTML`、`raw_html`、`unsafe_html`。
- 禁止 `html_allowed=true`。
- 禁止 `content` 中出现脚本、事件处理、内联样式和后端拼好的 HTML 片段。
- teacher 消息必须是 `plain_text`。
- assistant / xb 消息只能是 `safe_markdown` 或 `plain_text`。
- blocked payload 必须有 `blocking_reasons` 或 `unsafe_true_flags`。
- missing contract payload 不得处于可执行状态。
- 审核 ZIP 不包含前端页面、CSS、前端 JS、真实 runtime 接入文件、`.env`、`.openclaw` 或凭据类文件。

通过输出：

```text
ALL_071A_VALIDATIONS_OK
```

## 本轮没有做什么

- 未接 endpoint。
- 未接真实 runtime streaming。
- 未读取 `.openclaw`。
- 未接真实 Agent session。
- 未写飞书。
- 未写数据库。
- 未打开正式评分。
- 未打开正式导出。
- 未新增自动执行 Agent 的入口。
- 未新增 WebSocket。
- 未新增轮询。
- 未改变 069E / 069F 的安全边界。
- 未修改 `frontend/workbench/index.html`、CSS 或前端布局 JS。
- 未做 Markdown renderer。
- 未引入 markdown-it。
- 未返回后端渲染 HTML。

## 后续建议

071B 可以在继续保持 dry-run 和手动 gate 的前提下，设计一个后端纯函数：

```text
runtime response / dry-run response -> workbench_preview_viewmodel_071A_v0.1
```

071B 仍不建议直接接真实 streaming，也不建议让前端自动请求真实 Agent session。
