# Rule records

`knowledge/rules/<namespace>/<RULE_ID>.yaml`, namespaces `parashari` (PAR), `kp` (KP), `jaimini` (JAI), `shared` (SHR). One file per rule, holding every version, review and lifecycle event.

Full reference, lifecycle, examples and commands: [docs/rule-schema.md](../../docs/rule-schema.md).

```text
uv run jyotish rules validate              # check everything
uv run jyotish rules validate --against origin/main   # also: recorded history is append-only
uv run jyotish rules list
uv run jyotish rules seal PAR-ASP-0001     # write missing content_hash values
uv run jyotish rules approve PAR-ASP-0001 --version 1   # OWNER ONLY, interactive terminal
```

**This directory has no rule records yet.** Rules are written only from sources the owner has confirmed (Q-014). Claude Code drafts records as DRAFT or PROVISIONAL and never writes owner reviews or a VERIFIED status.
