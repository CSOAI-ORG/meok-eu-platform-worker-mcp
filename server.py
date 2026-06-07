#!/usr/bin/env python3
"""
MEOK EU Platform Workers Directive Compliance MCP
==================================================

By MEOK AI Labs · https://haulage.app · MIT
<!-- mcp-name: io.github.CSOAI-ORG/meok-eu-platform-worker-mcp -->

WHAT THIS DOES
--------------
Directive (EU) 2024/2831 on improving working conditions in platform work
("Platform Workers Directive") was published 11 Nov 2024 and must be
transposed by each Member State by 2 December 2026. It applies to digital
labour platforms operating in the EU and to all "platform workers" engaged
through them — irrespective of contractual label.

The Directive introduces:
- A rebuttable employment-status presumption (Art 5) triggered by 2+
  control indicators in member-state law (5 indicators in the EU Council
  text used as defaults here).
- Mandatory disclosure of automated monitoring + decision-making systems
  to workers and their representatives (Art 6).
- A right to human review of significant algorithmic decisions
  (restriction / suspension / termination / pay reduction) (Art 7).
- Data-minimisation + GDPR overlay for platform processing (Art 9).
- Consultation with worker reps before algorithmic management changes
  (Art 10).
- National transposition + designated competent authority by 2 Dec 2026
  (Art 29).

Platforms in scope: Uber, Bolt, Deliveroo, Just Eat Takeaway, Wolt, Glovo,
FREE NOW, plus delivery / freight / cleaning / care / micromobility apps.
EU gig economy: c.€20bn, c.28m workers (2025 EC estimate, of which 5.5m
estimated misclassified).

Precedents already enforcing parts of this:
- Spain "Ley Rider" Royal Decree-Law 9/2021 — first to legislate.
- Italian DL 152/2022 + Art 1bis algorithmic transparency.
- France 2016 + 2019 platform regimes (loi El Khomri / LOM).

TOOLS (8)
---------
- check_employment_status_presumption(worker_data)
- check_algorithmic_management_disclosure(platform_data)
- check_human_oversight_decisions(platform_data)
- check_worker_personal_data_protection(platform_data)
- check_algorithmic_transparency_consultation(platform_data)
- check_member_state_transposition(country_iso, transposition_date)
- forecast_misclassification_risk(operator_data)
- prepare_eu_platform_audit_pack(operator_data)

PRICING
-------
Free MIT self-host · €99 Starter · €299 Pro · €1,499 Fleet.

REGULATORY BASIS
----------------
- Directive (EU) 2024/2831 — Platform Work (transpose by 2 Dec 2026)
- Regulation (EU) 2016/679 — GDPR
- Spain Royal Decree-Law 9/2021 ("Ley Rider")
- Italy DL 152/2022 + Art 1bis algorithmic transparency
- UK Workers (Predictable Terms and Conditions) Act 2023 (UK comparator)
"""

from __future__ import annotations
import hashlib, hmac, json, os
from datetime import datetime, timezone, date
from typing import Optional
from mcp.server.fastmcp import FastMCP


mcp = FastMCP("meok-eu-platform-worker")
_HMAC_SECRET = os.environ.get("MEOK_HMAC_SECRET", "")


# ──────────────────────────────────────────────────────────────────────
# Regulatory tables — Directive (EU) 2024/2831
# ──────────────────────────────────────────────────────────────────────

# Art 5 — Employment-status presumption. The Directive sets a rebuttable
# presumption of employment when "facts indicating control and direction"
# are found. EU Council text retained 5 anchor indicators used by MS in
# transposition. Presumption triggers when ≥2 are met (national variation
# possible — Spain requires 1; some MS may require 3).
CONTROL_INDICATORS = {
    "remuneration_ceiling": "Platform sets the upper limit on remuneration",
    "appearance_or_conduct_rules": "Platform requires specific rules on appearance, conduct toward recipient, or work execution",
    "supervises_or_verifies_quality": "Platform supervises performance, including by electronic means, or verifies the quality of work results",
    "restricts_freedom_to_organise_work": "Platform effectively restricts freedom (incl. via sanctions) to choose working hours / accept or refuse tasks / use subcontractors or substitutes",
    "restricts_building_own_client_base": "Platform effectively restricts ability to build own client base or to perform work for a third party",
}
PRESUMPTION_TRIGGER_DEFAULT = 2  # default; Spain requires 1, some MS may require ≥3

# Art 6 — Disclosure of automated monitoring + decision-making to workers
AUTOMATED_DISCLOSURE_REQUIRED = {
    "automated_monitoring_systems",         # tracking, geolocation, time monitoring
    "automated_decision_systems",           # pay setting, task allocation, ratings, suspensions
    "data_categories_collected",            # personal data being processed
    "purposes_of_processing",
    "human_oversight_arrangements",
    "consequences_for_worker",              # how outputs affect tasks, pay, account status
}

# Art 7 — Human oversight: which decisions REQUIRE human review on request
SIGNIFICANT_DECISIONS_HUMAN_REVIEW = {
    "termination_of_account",
    "suspension_of_account",
    "restriction_of_account",
    "rejection_of_payment",
    "calculation_of_remuneration",  # esp. pay-per-task / dynamic-price algorithms
    "modification_of_contract_terms",
    "blocking_from_tasks_or_zones",
    "automated_dismissal_or_demotion",
}

# Art 8 — non-derogable obligations even where worker is genuinely self-employed
NON_DEROGABLE_FOR_SELF_EMPLOYED = {
    "transparency_of_automated_systems",
    "human_oversight_of_significant_decisions",
    "right_to_explanation_in_writing",
    "right_to_contest_decision",
}

# Art 9 — Data minimisation specific to platform work (GDPR-plus)
PROHIBITED_DATA_CATEGORIES = {
    "emotional_or_psychological_state",
    "private_conversations",
    "data_when_not_offering_or_performing_platform_work",
    "trade_union_activity_or_views",
    "race_or_ethnic_origin_for_targeting",
    "biometric_data_for_inference_of_personal_attributes",  # incl. mood / political
    "predicting_protected_characteristics",
}

# Art 10 — Worker-rep consultation thresholds
ALGORITHMIC_CHANGE_CONSULTATION_TRIGGERS = {
    "new_monitoring_system_introduced",
    "decision_logic_materially_changed",
    "pay_algorithm_modified",
    "task_allocation_algorithm_modified",
    "rating_or_reputation_system_modified",
    "geofencing_or_zone_blocking_introduced",
}

# Art 29 — Transposition deadline (each MS must publish national law by this date)
TRANSPOSITION_DEADLINE = date(2026, 12, 2)

# Country ISO -> known status of transposition (sample; updated as MS legislate)
KNOWN_NATIONAL_PRECURSORS = {
    "ES": {  # Spain — "Ley Rider" already in force
        "law": "Royal Decree-Law 9/2021",
        "in_force_since": "2021-08-12",
        "presumption_threshold": 1,
        "note": "Strict — single control indicator triggers presumption",
    },
    "IT": {  # Italy — DL 152/2022 algorithmic transparency
        "law": "DL 152/2022 + Art 1bis algorithmic transparency",
        "in_force_since": "2022-08-13",
        "presumption_threshold": 2,
        "note": "Algorithmic management disclosures predate 2024/2831",
    },
    "FR": {  # France — partial loi El Khomri / LOM
        "law": "Loi Travail 2016 + LOM 2019",
        "in_force_since": "2019-12-26",
        "presumption_threshold": 2,
        "note": "Voluntary platform charters; full Dir transposition pending",
    },
    "PT": {  # Portugal — Lei 13/2023
        "law": "Lei 13/2023 (Agenda do Trabalho Digno)",
        "in_force_since": "2023-05-01",
        "presumption_threshold": 2,
        "note": "Presumption of employment for platform riders codified",
    },
    "DE": {
        "law": "Transposition pending (BMAS draft)",
        "in_force_since": None,
        "presumption_threshold": 2,
        "note": "Awaiting national legislation",
    },
}

# Misclassification fine ranges per MS (EUR, indicative; from public regulator data)
MISCLASSIFICATION_FINE_RANGES_EUR = {
    "ES": {"per_worker_min": 7500, "per_worker_max": 225000, "back_pay_years": 4,
           "regulator": "ITSS — Inspección de Trabajo y Seguridad Social"},
    "IT": {"per_worker_min": 1500, "per_worker_max": 36000, "back_pay_years": 5,
           "regulator": "INL — Ispettorato Nazionale del Lavoro"},
    "FR": {"per_worker_min": 3000, "per_worker_max": 225000, "back_pay_years": 3,
           "regulator": "DIRECCTE / Inspection du Travail"},
    "DE": {"per_worker_min": 5000, "per_worker_max": 500000, "back_pay_years": 4,
           "regulator": "FKS — Finanzkontrolle Schwarzarbeit (Customs)"},
    "NL": {"per_worker_min": 4000, "per_worker_max": 87000, "back_pay_years": 5,
           "regulator": "NLA — Nederlandse Arbeidsinspectie"},
    "PT": {"per_worker_min": 2040, "per_worker_max": 61200, "back_pay_years": 5,
           "regulator": "ACT — Autoridade para as Condições do Trabalho"},
    "BE": {"per_worker_min": 1600, "per_worker_max": 48000, "back_pay_years": 5,
           "regulator": "SIRS — Service d'Information et de Recherche Sociale"},
    "PL": {"per_worker_min": 1000, "per_worker_max": 30000, "back_pay_years": 3,
           "regulator": "PIP — Państwowa Inspekcja Pracy"},
}

# EU-27 ISO codes — used to scope transposition checks
EU_27 = {
    "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "GR",
    "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL", "PL", "PT", "RO", "SK",
    "SI", "ES", "SE",
}


# ──────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────

def _sign(payload: dict) -> str:
    if not _HMAC_SECRET:
        return "unsigned-no-key-configured"
    return hmac.new(_HMAC_SECRET.encode(),
                    json.dumps(payload, sort_keys=True, default=str).encode(),
                    hashlib.sha256).hexdigest()


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


def _attestation(payload: dict) -> dict:
    return {**payload, "ts": _ts(), "sig": _sign(payload),
            "issuer": "meok-eu-platform-worker-mcp", "version": "1.0.0"}


# ──────────────────────────────────────────────────────────────────────
# Tools
# ──────────────────────────────────────────────────────────────────────

@mcp.tool()
def check_employment_status_presumption(
    worker_name: str = "",
    platform_name: str = "",
    member_state_iso: str = "",
    indicators_present: Optional[list] = None,
) -> dict:
    """Directive (EU) 2024/2831 Art 5 — rebuttable employment-status presumption.

    Args:
      indicators_present: subset of CONTROL_INDICATORS keys, e.g.
        ["remuneration_ceiling", "supervises_or_verifies_quality"]
      member_state_iso: ISO country code; if MS is in KNOWN_NATIONAL_PRECURSORS
        the local threshold is used (Spain = 1), else default = 2.
    """
    indicators_present = indicators_present or []
    valid = [i for i in indicators_present if i in CONTROL_INDICATORS]
    invalid = [i for i in indicators_present if i not in CONTROL_INDICATORS]

    ms = member_state_iso.upper()
    if ms in KNOWN_NATIONAL_PRECURSORS:
        threshold = KNOWN_NATIONAL_PRECURSORS[ms]["presumption_threshold"]
        threshold_basis = f"national precursor: {KNOWN_NATIONAL_PRECURSORS[ms]['law']}"
    else:
        threshold = PRESUMPTION_TRIGGER_DEFAULT
        threshold_basis = "EU 2024/2831 default (≥2 indicators)"

    presumed_employee = len(valid) >= threshold

    return _attestation({
        "tool": "check_employment_status_presumption",
        "worker": worker_name,
        "platform": platform_name,
        "member_state": ms,
        "indicators_present": valid,
        "indicators_invalid": invalid,
        "indicators_count": len(valid),
        "presumption_threshold": threshold,
        "threshold_basis": threshold_basis,
        "presumed_employee": presumed_employee,
        "rebuttal_available": presumed_employee,  # platform can rebut by proving lack of control
        "advisory": (
            "Employment presumed — burden on platform to rebut. Misclassification "
            "exposure: back-pay social-security + payroll tax + fines per MS."
            if presumed_employee else
            "Below national threshold — no presumption triggered on submitted indicators."
        ),
        "regulator_ref": "Directive (EU) 2024/2831 Art 5",
    })


@mcp.tool()
def check_algorithmic_management_disclosure(
    platform_name: str = "",
    disclosed_items: Optional[list] = None,
    disclosure_channel: str = "",
    languages_provided: Optional[list] = None,
) -> dict:
    """Directive (EU) 2024/2831 Art 6 — Disclosure of automated monitoring +
    decision systems to workers and their representatives.

    Args:
      disclosed_items: subset of AUTOMATED_DISCLOSURE_REQUIRED that platform
        has documented + published to workers.
      disclosure_channel: e.g. "in-app notice", "worker portal", "email"
      languages_provided: list of ISO 639 language codes the disclosure is in
    """
    disclosed_items = set(disclosed_items or [])
    languages_provided = languages_provided or []

    missing = sorted(AUTOMATED_DISCLOSURE_REQUIRED - disclosed_items)
    extra = sorted(disclosed_items - AUTOMATED_DISCLOSURE_REQUIRED)

    multilingual = len(languages_provided) >= 1
    compliant = (not missing) and bool(disclosure_channel) and multilingual

    return _attestation({
        "tool": "check_algorithmic_management_disclosure",
        "platform": platform_name,
        "disclosed_items": sorted(disclosed_items),
        "missing_items": missing,
        "extra_items": extra,
        "disclosure_channel": disclosure_channel,
        "languages_provided": languages_provided,
        "multilingual_disclosure": multilingual,
        "compliant": compliant,
        "issue": "" if compliant else "Disclosure incomplete — Art 6 requires written, intelligible info before processing begins",
        "regulator_ref": "Directive (EU) 2024/2831 Art 6",
    })


@mcp.tool()
def check_human_oversight_decisions(
    platform_name: str = "",
    decisions_with_human_review: Optional[list] = None,
    review_sla_business_days: int = 0,
    written_reasoning_provided: bool = False,
) -> dict:
    """Directive (EU) 2024/2831 Art 7 — Significant decisions (firing, blocking,
    pay reduction) must be reviewable by a human on worker request, with
    written reasoning.

    Args:
      decisions_with_human_review: subset of SIGNIFICANT_DECISIONS_HUMAN_REVIEW
        for which the platform has implemented a human-review channel.
      review_sla_business_days: how many business days the platform commits to
        respond to a review request (Directive guidance: "without undue delay",
        public regulator expectation: ≤10 business days).
      written_reasoning_provided: whether each significant decision is
        accompanied by written reasoning at the time of decision.
    """
    covered = set(decisions_with_human_review or [])
    missing = sorted(SIGNIFICANT_DECISIONS_HUMAN_REVIEW - covered)
    sla_ok = 0 < review_sla_business_days <= 10
    compliant = (not missing) and sla_ok and written_reasoning_provided

    issues = []
    if missing:
        issues.append(f"No human review available for: {', '.join(missing)}")
    if not sla_ok:
        issues.append(f"Review SLA {review_sla_business_days}d outside 1–10 business-day window")
    if not written_reasoning_provided:
        issues.append("Written reasoning not provided at decision time")

    return _attestation({
        "tool": "check_human_oversight_decisions",
        "platform": platform_name,
        "decisions_covered": sorted(covered),
        "decisions_missing": missing,
        "review_sla_business_days": review_sla_business_days,
        "review_sla_acceptable": sla_ok,
        "written_reasoning_provided": written_reasoning_provided,
        "compliant": compliant,
        "issues": issues,
        "non_derogable_for_self_employed": sorted(NON_DEROGABLE_FOR_SELF_EMPLOYED),
        "regulator_ref": "Directive (EU) 2024/2831 Art 7 (+ Art 8 non-derogable)",
    })


@mcp.tool()
def check_worker_personal_data_protection(
    platform_name: str = "",
    data_categories_processed: Optional[list] = None,
    dpia_completed: bool = False,
    retention_max_days: int = 0,
) -> dict:
    """Directive (EU) 2024/2831 Art 9 — data minimisation + GDPR overlay
    specific to platform work.

    Args:
      data_categories_processed: list of platform-defined data categories
        currently processed (each will be checked against the
        PROHIBITED_DATA_CATEGORIES blocklist).
      dpia_completed: GDPR Art 35 DPIA covering the platform-management system.
      retention_max_days: maximum retention applied to worker telemetry /
        ratings data.
    """
    categories = set(data_categories_processed or [])
    prohibited_in_use = sorted(categories & PROHIBITED_DATA_CATEGORIES)
    retention_ok = 0 < retention_max_days <= 730   # 24 months reasonable upper bound
    compliant = (not prohibited_in_use) and dpia_completed and retention_ok

    issues = []
    if prohibited_in_use:
        issues.append(f"Prohibited categories in use: {', '.join(prohibited_in_use)}")
    if not dpia_completed:
        issues.append("GDPR Art 35 DPIA not completed for platform-management system")
    if not retention_ok:
        issues.append(f"Retention {retention_max_days}d unjustified (>24 months or unset)")

    return _attestation({
        "tool": "check_worker_personal_data_protection",
        "platform": platform_name,
        "data_categories_processed": sorted(categories),
        "prohibited_categories_in_use": prohibited_in_use,
        "dpia_completed": dpia_completed,
        "retention_max_days": retention_max_days,
        "compliant": compliant,
        "issues": issues,
        "regulator_ref": "Directive (EU) 2024/2831 Art 9 + GDPR (EU) 2016/679 Art 5 + 35",
    })


@mcp.tool()
def check_algorithmic_transparency_consultation(
    platform_name: str = "",
    planned_changes: Optional[list] = None,
    worker_representatives_consulted: bool = False,
    consultation_notice_days: int = 0,
    written_record_kept: bool = False,
) -> dict:
    """Directive (EU) 2024/2831 Art 10 — consultation with worker reps before
    material algorithmic-management changes.

    Args:
      planned_changes: subset of ALGORITHMIC_CHANGE_CONSULTATION_TRIGGERS that
        the platform intends to introduce.
      worker_representatives_consulted: whether reps have been notified +
        consulted before deployment.
      consultation_notice_days: lead time given before the change goes live
        (regulator guidance: ≥14 calendar days for material change).
      written_record_kept: whether the consultation outcome is documented.
    """
    planned = set(planned_changes or [])
    invalid_changes = sorted(planned - ALGORITHMIC_CHANGE_CONSULTATION_TRIGGERS)
    triggering = sorted(planned & ALGORITHMIC_CHANGE_CONSULTATION_TRIGGERS)
    requires_consultation = bool(triggering)
    notice_ok = consultation_notice_days >= 14
    compliant = (not requires_consultation) or (
        worker_representatives_consulted and notice_ok and written_record_kept
    )

    issues = []
    if requires_consultation:
        if not worker_representatives_consulted:
            issues.append("Worker reps not consulted before triggering change")
        if not notice_ok:
            issues.append(f"Notice period {consultation_notice_days}d < 14d guidance")
        if not written_record_kept:
            issues.append("No written record of consultation outcome")

    return _attestation({
        "tool": "check_algorithmic_transparency_consultation",
        "platform": platform_name,
        "triggering_changes": triggering,
        "invalid_changes": invalid_changes,
        "requires_consultation": requires_consultation,
        "worker_representatives_consulted": worker_representatives_consulted,
        "consultation_notice_days": consultation_notice_days,
        "written_record_kept": written_record_kept,
        "compliant": compliant,
        "issues": issues,
        "regulator_ref": "Directive (EU) 2024/2831 Art 10",
    })


@mcp.tool()
def check_member_state_transposition(
    country_iso: str,
    transposition_date: str = "",
) -> dict:
    """Directive (EU) 2024/2831 Art 29 — MS must transpose by 2 Dec 2026.

    Args:
      country_iso: ISO country code (EU-27 expected)
      transposition_date: ISO date the national transposition act enters into
        force (use empty string if unknown / not yet transposed).
    """
    iso = country_iso.upper()
    in_eu = iso in EU_27
    precursor = KNOWN_NATIONAL_PRECURSORS.get(iso)

    try:
        transposed = date.fromisoformat(transposition_date) if transposition_date else None
    except Exception:
        transposed = None

    today = date.today()
    if transposed:
        on_time = transposed <= TRANSPOSITION_DEADLINE
        days_to_deadline = (TRANSPOSITION_DEADLINE - transposed).days
        status = "transposed"
    else:
        on_time = False
        days_to_deadline = (TRANSPOSITION_DEADLINE - today).days
        status = "pending"

    return _attestation({
        "tool": "check_member_state_transposition",
        "country_iso": iso,
        "in_eu_27": in_eu,
        "transposition_deadline": TRANSPOSITION_DEADLINE.isoformat(),
        "national_transposition_date": transposed.isoformat() if transposed else None,
        "status": status,
        "on_time_vs_deadline": on_time,
        "days_to_deadline": days_to_deadline,
        "national_precursor": precursor,
        "advisory": (
            "MS has missed the 2 Dec 2026 deadline — Commission infringement risk; "
            "Directive may be directly invoked against state emanations."
            if status == "pending" and days_to_deadline < 0 else
            "Transposition timing acceptable"
            if status == "transposed" and on_time else
            "Watch the clock — under 90 days to deadline."
            if status == "pending" and 0 <= days_to_deadline <= 90 else
            "Pending — within ordinary transposition runway."
        ),
        "regulator_ref": "Directive (EU) 2024/2831 Art 29",
    })


@mcp.tool()
def forecast_misclassification_risk(
    operator_name: str = "",
    member_state_iso: str = "",
    workers_at_risk: int = 0,
    avg_monthly_revenue_per_worker_eur: float = 0.0,
    months_of_exposure: int = 12,
) -> dict:
    """Forecast fines + back-pay exposure if presumption is applied and
    workers are reclassified as employees (Spain "Ley Rider" precedent —
    Glovo, Deliveroo Spain settled c.€79m + c.€34m respectively).

    Returns a low/central/high estimate. Inputs are operator-supplied;
    this tool does not validate them.
    """
    ms = member_state_iso.upper()
    fr = MISCLASSIFICATION_FINE_RANGES_EUR.get(ms)

    if not fr:
        return _attestation({
            "tool": "forecast_misclassification_risk",
            "operator": operator_name,
            "member_state": ms,
            "error": f"No published fine range for MS '{ms}' — manual review required",
            "regulator_ref": "Directive (EU) 2024/2831 Art 5 (per MS enforcement)",
        })

    workers = max(0, workers_at_risk)
    months = max(1, months_of_exposure)

    fines_low = workers * fr["per_worker_min"]
    fines_central = workers * (fr["per_worker_min"] + fr["per_worker_max"]) / 2
    fines_high = workers * fr["per_worker_max"]

    # Back-pay: estimated employer-side cost = ~30% social-security + payroll tax
    # over months of exposure, capped at MS back-pay years.
    capped_months = min(months, fr["back_pay_years"] * 12)
    back_pay_per_worker = avg_monthly_revenue_per_worker_eur * capped_months * 0.30
    back_pay_total = workers * back_pay_per_worker

    return _attestation({
        "tool": "forecast_misclassification_risk",
        "operator": operator_name,
        "member_state": ms,
        "regulator": fr["regulator"],
        "workers_at_risk": workers,
        "months_modelled": months,
        "capped_months_for_back_pay": capped_months,
        "fines_eur": {
            "low": round(fines_low),
            "central": round(fines_central),
            "high": round(fines_high),
        },
        "estimated_back_pay_eur": round(back_pay_total),
        "total_exposure_central_eur": round(fines_central + back_pay_total),
        "precedent_note": "Spain ITSS treated Glovo/Deliveroo riders as employees; "
                          "combined settlements/fines exceeded €100m (2021–2023).",
        "regulator_ref": "Directive (EU) 2024/2831 Art 5 + national labour-inspection statutes",
    })


@mcp.tool()
def prepare_eu_platform_audit_pack(
    operator_name: str,
    operator_country: str,
    workers_engaged: int = 0,
    member_states_active: Optional[list] = None,
) -> dict:
    """Generate the evidence-pack skeleton for national enforcement (LabBoard /
    ITSS / INL / ACT / FKS / SIRS / NLA / PIP)."""
    return _attestation({
        "tool": "prepare_eu_platform_audit_pack",
        "operator": operator_name,
        "operator_country": operator_country.upper(),
        "workers_engaged": workers_engaged,
        "member_states_active": [m.upper() for m in (member_states_active or [])],
        "evidence_sections": [
            {"section": "I. Worker engagement register — contractual basis per worker"},
            {"section": "II. Control-indicator self-assessment vs Art 5 (per worker class)"},
            {"section": "III. Algorithmic-management disclosure pack (Art 6) per language"},
            {"section": "IV. Human-oversight workflow — Art 7 SLA + reviewer roster"},
            {"section": "V. GDPR Art 35 DPIA + Art 9 data-minimisation register"},
            {"section": "VI. Worker-rep consultation log (Art 10) — last 24 months"},
            {"section": "VII. National-law overlay per active MS (Ley Rider / DL 152 / Lei 13/2023…)"},
            {"section": "VIII. Misclassification-risk forecast + reserve disclosure"},
            {"section": "IX. Incident log — automated decisions overturned on review"},
            {"section": "X. Annual report to designated competent authority (Art 12)"},
            {"section": "XI. Cross-border data-transfer register (GDPR Ch V)"},
        ],
        "advisory": "Pack supports member-state labour-inspection enforcement — "
                    "operator's legal team must review per host MS. Spain ITSS, "
                    "Italy INL, France DIRECCTE, Germany FKS, Netherlands NLA, "
                    "Portugal ACT, Belgium SIRS, Poland PIP are the leading "
                    "enforcement bodies.",
        "regulator_ref": "Directive (EU) 2024/2831 Art 12 (national competent authority)",
    })


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()


# ── MEOK monetization layer (Stripe upgrade · PAYG · pricing) ──────────
# Free tier is zero-config. Upgrade to Pro (unlimited) or pay-as-you-go per call.
import os as _meok_os
MEOK_STRIPE_UPGRADE = "https://buy.stripe.com/5kQ6oJ0xS3ce8sl7ew8k91j"  # Pro (unlimited)
MEOK_PAYG_KEY = _meok_os.environ.get("MEOK_PAYG_KEY", "")  # set to enable PAYG (x402 / ~GBP0.05 per call)
MEOK_PRICING = "https://meok.ai/pricing"


def meok_upsell(tier: str = "free") -> dict:
    """Monetization options for free-tier callers: Pro upgrade, PAYG, or pricing page."""
    if tier != "free":
        return {}
    return {"upgrade_url": MEOK_STRIPE_UPGRADE,
            "payg_enabled": bool(MEOK_PAYG_KEY),
            "pricing": MEOK_PRICING}
