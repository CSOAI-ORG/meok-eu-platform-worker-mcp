<!-- mcp-name: io.github.CSOAI-ORG/meok-eu-platform-worker-mcp -->
[![MCP Scorecard: 90/100](https://img.shields.io/badge/proofof.ai-90%2F100-5b21b6)](https://proofof.ai/scorecard/meok-eu-platform-worker-mcp.html)

# meok-eu-platform-worker-mcp

> EU Platform Workers Directive (2024/2831) compliance for digital labour platforms operating in the EU. Employment-status presumption, algorithmic-management disclosure, human oversight, GDPR overlay, member-state transposition tracking, misclassification-risk forecast. By **MEOK AI Labs**.

## Why this exists

Directive (EU) 2024/2831 must be transposed into national law by every Member State by **2 December 2026**. It applies to digital labour platforms — Deliveroo, Just Eat Takeaway, Uber, Bolt, Wolt, Glovo, FREE NOW — plus thousands of smaller delivery / freight / cleaning / care / micromobility apps. The EU gig economy is c.€20bn and c.28m workers (2025 EC estimate, of which c.5.5m estimated misclassified).

Spain's "Ley Rider" (Royal Decree-Law 9/2021) already established that platform riders are presumed employees. ITSS enforcement produced settlements / fines exceeding €100m against Glovo + Deliveroo Spain by 2023. The Directive generalises that precedent across all 27 MS.

This MCP gives platforms (and their compliance counsel) a callable layer for the daily work:

- Art 5 employment-status presumption — count the control indicators.
- Art 6 disclosure of monitoring + decision systems — closed-list checker.
- Art 7 human oversight of significant decisions — gap analysis + SLA.
- Art 9 worker-data minimisation — prohibited-category blocklist + GDPR overlay.
- Art 10 worker-rep consultation — change-trigger detection.
- Art 29 transposition tracker per MS — 2 Dec 2026 cliff.
- Misclassification fines + back-pay forecaster — 8 MS calibrated.
- National-enforcement evidence pack generator.

## Install

```bash
pip install meok-eu-platform-worker-mcp
```

## Tools (8)

| Tool | Use case |
|------|----------|
| `check_employment_status_presumption` | Art 5 — count control indicators against MS threshold |
| `check_algorithmic_management_disclosure` | Art 6 — disclosure of monitoring + decision systems |
| `check_human_oversight_decisions` | Art 7 — human review of significant decisions |
| `check_worker_personal_data_protection` | Art 9 — data minimisation + GDPR overlay |
| `check_algorithmic_transparency_consultation` | Art 10 — worker-rep consultation before changes |
| `check_member_state_transposition` | Art 29 — Dec 2026 transposition deadline per MS |
| `forecast_misclassification_risk` | Fines + back-pay exposure (8 MS calibrated) |
| `prepare_eu_platform_audit_pack` | Evidence pack for ITSS / INL / ACT / FKS / SIRS / NLA / PIP / DIRECCTE |

## Pricing

- **Free** — MIT self-host
- **Starter** — €99/mo (single platform, single MS)
- **Pro** — €299/mo (multi-MS, full audit pack)
- **Fleet** — €1,499/mo (cross-MS misclassification reserve modelling + named CSM)

## Regulatory basis

- Directive (EU) 2024/2831 — Platform Work (transposition deadline 2 Dec 2026)
- Regulation (EU) 2016/679 — GDPR (Arts 5, 22, 35 overlay)
- Spain Royal Decree-Law 9/2021 — "Ley Rider" (precedent)
- Italy DL 152/2022 + Art 1bis algorithmic transparency
- Portugal Lei 13/2023 (Agenda do Trabalho Digno) — rider presumption
- France Loi Travail 2016 + LOM 2019 (partial regime)
- UK Workers (Predictable Terms and Conditions) Act 2023 (UK comparator)

## License

MIT © 2026 Nicholas Templeman / MEOK AI Labs · [haulage.app](https://haulage.app)


## Configuration

Add to your `claude_desktop_config.json` (Claude Desktop) or your MCP client config:

```json
{
  "mcpServers": {
    "meok-eu-platform-worker-mcp": {
      "command": "uvx",
      "args": ["meok-eu-platform-worker-mcp"]
    }
  }
}
```

Or: `pip install meok-eu-platform-worker-mcp` then run the `meok-eu-platform-worker-mcp` command (stdio transport).

## Examples

Once configured, ask your assistant, for example:
- "Use `check_employment_status_presumption` to …"
- "Use `check_algorithmic_management_disclosure` to …"
- "Use `check_human_oversight_decisions` to …"


<!-- GEO-FOOTER:v1 -->

---

### Part of the MEOK constellation

This MCP is one node in a connected ecosystem built by **MEOK AI LABS** around a single
sovereign AI core — governed agents with a hash-chained audit trail, mapped to the CSOAI
compliance charter.

- 🌐 The whole map: **<https://meok.ai/constellation>**
- 🛡️ AI governance & certification: **<https://councilof.ai>** · **<https://csoai.org>**
- ✅ Verify any signed report: **<https://meok.ai/verify>**
