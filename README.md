# cognic-skill-warehouse-data

Instruction-only governed AgentOS skill for warehouse revenue, units,
channels, promotions, and calendar/fiscal analysis over the Oracle SH sample
schema. It carries guidance and a golden corpus; it has no executable entry
point and no runtime dependencies.

| contract | value |
|---|---|
| skill id | `warehouse-data` |
| mode | `instruction` |
| scope taught | `warehouse` |
| governed tool | `cognic-tool-oracle-schema/run_readonly_query` |
| views | `SH.V_SALES_STAR`, `SH.V_CALENDAR`, `SH.V_PROMOTIONS`, `SH.V_SALES_BY_CHANNEL` |
| risk tier | `read_only` |
| corpus | 26 ratified cases in `golden/queries.jsonl` |

The kernel hosts `SKILL.md` read-only. Authority remains in the asking user's
assignment, data-scope entitlement, signed query context, and Oracle view-only
proxy identity. `referenced_tools` is reviewer evidence, not an authorization
grant.

The corpus deliberately keeps `sh-104` as a judge-scored performance case:
its direct `TIME_ID` range tests partition-friendly SQL shape, not only the
returned number. That open scoring exception is not resolved in v0.1.0.

## Development

```sh
uv lock --check
uv sync --frozen --extra dev
uv run --extra dev pytest -q
uv run --extra dev ruff check src tests
uv run --extra dev ruff format --check src tests
uv run --extra dev mypy src tests
```

`agentos validate .` additionally requires the declared attestation files.
CI creates non-publishable placeholders only for that shape check. The real
wheel and attestation bundle are produced by the protected release lane under
operator signing-key custody; release assets are never committed.
