# 071B Workbench Preview ViewModel Builder Dry-Run

## 目标

071B 新增一个纯函数 builder：

```text
backend/xiaobei_ai/workbench_preview_viewmodel_builder_071B.py
```

入口：

```python
build_workbench_preview_viewmodel(input_payload: dict) -> dict
```

它把 dry-run response / candidate response / guard result / trace preview 统一归一化为 `071A / 071B0` 的 Workbench Preview ViewModel。071B 不接 endpoint，不接真实 runtime，不接 streaming。

## 和 071A / 071B0 的关系

071A 定义 ViewModel 顶层契约。

071B0 锁定消息内容边界：后端只输出 `content + content_format + render_policy`，不输出 HTML，不做 Markdown 渲染。

071B 在这个边界内实现纯函数 builder，让后续 `071C` 如果要做 dry-run endpoint，可以复用同一套归一化逻辑。

## Builder 输入结构

071B 输入可以是较干净的 ViewModel-like payload：

```text
source
gates
messages 或 left_chat.messages
right_workspace.doc_sections
candidate_blocks
trace.events
actions
verifier
```

也可以是接近 dry-run response 的 payload：

```text
teacher_message
assistant_message
card_updates
```

Builder 会尽量读取这些字段，但只输出 071A/071B0 允许的结构。

## Builder 输出结构

输出固定包含：

```text
viewmodel_version
mode
source
gates
left_chat
right_workspace
candidate_blocks
verifier
trace
actions
audit
```

固定值：

```text
viewmodel_version=workbench_preview_viewmodel_071A_v0.1
mode=dry_run
```

## 危险 gate 收口策略

以下 gate 永远输出为 `false`：

```text
can_score
formal_scoring_allowed
formal_writeback_allowed
feishu_write_allowed
kb_ingest_allowed
frontend_connect_allowed
runtime_streaming_allowed
export_allowed
```

`teacher_review_required` 永远输出为 `true`。

如果输入中出现危险 true，Builder 会：

```text
1. 将输出 gates 收口为 false
2. 将 verifier.status 置为 blocked
3. 在 audit.unsafe_true_flags 中记录危险路径
4. 在 audit.normalization_notes 中说明已收口
```

## content_format / render_policy 策略

Builder 遵守 071B0：

```text
teacher -> plain_text
assistant / xb -> safe_markdown 或 plain_text
system -> plain_text
right_workspace.doc_sections -> content + content_format + render_policy
candidate_blocks -> content + content_format + render_policy
```

所有可显示内容都带：

```json
{
  "render_policy": {
    "html_allowed": false,
    "frontend_render_required": true,
    "sanitize_required": true
  }
}
```

如果输入声明 `content_format=html`，Builder 会降级为 `plain_text`，并写入 audit。若输入含 `<script`、`onclick=`、`style=` 或 `javascript:` 等片段，Builder 会中和这些片段，仍由前端按文本或安全 Markdown 渲染。

后端仍不做 Markdown renderer，不引入 markdown-it，不输出 HTML。

## trace preview 策略

071B 只做静态 trace preview：

```text
trace.events[] -> event_id / event_type / label / status / message / timestamp
```

没有 WebSocket，没有轮询，不读取真实 runtime events，不连接 OpenClaw session。

## actions.disabled 策略

输出 actions 只做建议，不可执行。

Builder 总是禁用：

```text
formal_writeback
formal_scoring
feishu_write
runtime_streaming
formal_export
kb_ingest
```

这些动作只用于前端展示“为什么现在不能做”，不会触发真实写入、评分、导出或 streaming。

## 三个样例

### input_safe_dry_run.json -> output_safe_viewmodel.json

正常 dry-run 输入，包含 contract、assignment、teacher message、assistant markdown、doc_sections、candidate_blocks 和 trace。

输出：

```text
verifier.status=pending_review
危险 gates 全 false
left_chat/right_workspace/candidate_blocks 可用于前端预览
```

### input_guard_blocked.json -> output_blocked_viewmodel.json

模拟上游错误打开危险能力。

输出：

```text
verifier.status=blocked
危险 gates 全 false
audit.unsafe_true_flags 非空
audit.normalization_notes 非空
actions.disabled 说明不能评分/写入/导出/streaming
```

### input_missing_contract.json -> output_missing_contract_viewmodel.json

模拟缺少 `contract_id` 和 `assignment_id`。

输出：

```text
verifier.status=blocked
blocking_reasons 说明缺 contract_id / assignment_id
frontend_connect_allowed=false
export_allowed=false
不得自动补成可执行状态
```

## 校验命令

```text
python scripts/validate_workbench_preview_viewmodel_builder_071B.py
```

预期输出：

```text
ALL_071B_BUILDER_DRY_RUN_CHECKS_OK
```

## 本轮没有做什么

- 没有 endpoint。
- 没有 runtime。
- 没有 streaming。
- 没有读取 `.openclaw`。
- 没有接真实 Agent session。
- 没有写入飞书。
- 没有写入数据库。
- 没有打开评分。
- 没有打开导出。
- 没有评分。
- 没有导出。
- 没有 WebSocket。
- 没有自动轮询。
- 没有改前端。
- 没有改 CSS。
- 没有改前端 JS。
- 没有做 Markdown renderer。
- 没有引入 markdown-it。

## 后续建议

下一步可以进入：

```text
071C：Preview ViewModel Dry-Run Endpoint
```

071C 也建议继续保持 dry-run endpoint，只返回 ViewModel，不接真实 streaming，不打开写入、评分、导出。
