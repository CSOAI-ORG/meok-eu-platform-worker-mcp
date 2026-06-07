"""Smoke tests for meok-eu-platform-worker-mcp."""
import sys, os, hashlib, hmac as _hmac, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import server as server_mod
from server import (
    check_employment_status_presumption,
    check_algorithmic_management_disclosure,
    check_human_oversight_decisions,
    check_worker_personal_data_protection,
    check_algorithmic_transparency_consultation,
    check_member_state_transposition,
    forecast_misclassification_risk,
    prepare_eu_platform_audit_pack,
    CONTROL_INDICATORS,
    AUTOMATED_DISCLOSURE_REQUIRED,
    SIGNIFICANT_DECISIONS_HUMAN_REVIEW,
    PROHIBITED_DATA_CATEGORIES,
    ALGORITHMIC_CHANGE_CONSULTATION_TRIGGERS,
    KNOWN_NATIONAL_PRECURSORS,
    MISCLASSIFICATION_FINE_RANGES_EUR,
    TRANSPOSITION_DEADLINE,
    EU_27,
)


def _call(t, **kw):
    fn = t.fn if hasattr(t, "fn") else t
    return fn(**kw)


# ── Art 5 — employment-status presumption ─────────────────────────────

def test_presumption_default_threshold_triggered():
    r = _call(check_employment_status_presumption,
              worker_name="Marek", platform_name="Deliveroo",
              member_state_iso="DE",
              indicators_present=["remuneration_ceiling",
                                  "supervises_or_verifies_quality"])
    assert r["presumed_employee"] is True
    assert r["presumption_threshold"] == 2
    assert r["indicators_count"] == 2


def test_presumption_default_threshold_not_met():
    r = _call(check_employment_status_presumption,
              worker_name="Anya", platform_name="Bolt",
              member_state_iso="DE",
              indicators_present=["remuneration_ceiling"])
    assert r["presumed_employee"] is False
    assert r["indicators_count"] == 1


def test_presumption_spain_single_indicator_triggers():
    # Spain's Ley Rider: threshold = 1
    r = _call(check_employment_status_presumption,
              worker_name="Pablo", platform_name="Glovo",
              member_state_iso="ES",
              indicators_present=["remuneration_ceiling"])
    assert r["presumption_threshold"] == 1
    assert r["presumed_employee"] is True
    assert "Royal Decree-Law 9/2021" in r["threshold_basis"]


def test_presumption_filters_invalid_indicators():
    r = _call(check_employment_status_presumption,
              worker_name="Z", member_state_iso="FR",
              indicators_present=["remuneration_ceiling", "made_up_indicator"])
    assert "made_up_indicator" in r["indicators_invalid"]
    assert r["indicators_count"] == 1


# ── Art 6 — algorithmic-management disclosure ─────────────────────────

def test_disclosure_complete_compliant():
    r = _call(check_algorithmic_management_disclosure,
              platform_name="Wolt",
              disclosed_items=list(AUTOMATED_DISCLOSURE_REQUIRED),
              disclosure_channel="in-app notice",
              languages_provided=["en", "de"])
    assert r["compliant"] is True
    assert r["missing_items"] == []


def test_disclosure_missing_items_fails():
    r = _call(check_algorithmic_management_disclosure,
              platform_name="Just Eat",
              disclosed_items=["automated_monitoring_systems"],
              disclosure_channel="email",
              languages_provided=["en"])
    assert r["compliant"] is False
    assert len(r["missing_items"]) >= 4


def test_disclosure_no_language_fails():
    r = _call(check_algorithmic_management_disclosure,
              platform_name="X",
              disclosed_items=list(AUTOMATED_DISCLOSURE_REQUIRED),
              disclosure_channel="portal",
              languages_provided=[])
    assert r["compliant"] is False
    assert r["multilingual_disclosure"] is False


# ── Art 7 — human oversight ────────────────────────────────────────────

def test_human_oversight_full_coverage_compliant():
    r = _call(check_human_oversight_decisions,
              platform_name="Uber",
              decisions_with_human_review=list(SIGNIFICANT_DECISIONS_HUMAN_REVIEW),
              review_sla_business_days=5,
              written_reasoning_provided=True)
    assert r["compliant"] is True


def test_human_oversight_missing_decisions_fails():
    r = _call(check_human_oversight_decisions,
              platform_name="FREE NOW",
              decisions_with_human_review=["termination_of_account"],
              review_sla_business_days=5,
              written_reasoning_provided=True)
    assert r["compliant"] is False
    assert "termination_of_account" not in r["decisions_missing"]
    assert "suspension_of_account" in r["decisions_missing"]


def test_human_oversight_bad_sla_fails():
    r = _call(check_human_oversight_decisions,
              platform_name="P",
              decisions_with_human_review=list(SIGNIFICANT_DECISIONS_HUMAN_REVIEW),
              review_sla_business_days=30,
              written_reasoning_provided=True)
    assert r["compliant"] is False
    assert r["review_sla_acceptable"] is False


# ── Art 9 — worker data protection ─────────────────────────────────────

def test_data_protection_clean_compliant():
    r = _call(check_worker_personal_data_protection,
              platform_name="P",
              data_categories_processed=["delivery_geolocation", "order_history"],
              dpia_completed=True,
              retention_max_days=365)
    assert r["compliant"] is True
    assert r["prohibited_categories_in_use"] == []


def test_data_protection_prohibited_category_fails():
    r = _call(check_worker_personal_data_protection,
              platform_name="BadCo",
              data_categories_processed=[
                  "delivery_geolocation",
                  "emotional_or_psychological_state",  # prohibited
              ],
              dpia_completed=True,
              retention_max_days=365)
    assert r["compliant"] is False
    assert "emotional_or_psychological_state" in r["prohibited_categories_in_use"]


def test_data_protection_missing_dpia_fails():
    r = _call(check_worker_personal_data_protection,
              platform_name="P",
              data_categories_processed=["geolocation"],
              dpia_completed=False,
              retention_max_days=180)
    assert r["compliant"] is False


# ── Art 10 — consultation ──────────────────────────────────────────────

def test_consultation_required_and_done():
    r = _call(check_algorithmic_transparency_consultation,
              platform_name="P",
              planned_changes=["pay_algorithm_modified"],
              worker_representatives_consulted=True,
              consultation_notice_days=21,
              written_record_kept=True)
    assert r["compliant"] is True
    assert r["requires_consultation"] is True


def test_consultation_missing_notice_fails():
    r = _call(check_algorithmic_transparency_consultation,
              platform_name="P",
              planned_changes=["new_monitoring_system_introduced"],
              worker_representatives_consulted=True,
              consultation_notice_days=3,
              written_record_kept=True)
    assert r["compliant"] is False


def test_consultation_no_triggers_no_consultation_needed():
    r = _call(check_algorithmic_transparency_consultation,
              platform_name="P", planned_changes=[],
              worker_representatives_consulted=False,
              consultation_notice_days=0,
              written_record_kept=False)
    assert r["requires_consultation"] is False
    assert r["compliant"] is True


# ── Art 29 — transposition ─────────────────────────────────────────────

def test_transposition_spain_already_in_force():
    r = _call(check_member_state_transposition,
              country_iso="ES", transposition_date="2021-08-12")
    assert r["status"] == "transposed"
    assert r["on_time_vs_deadline"] is True
    assert r["national_precursor"]["law"].startswith("Royal Decree-Law")


def test_transposition_germany_pending():
    r = _call(check_member_state_transposition,
              country_iso="DE", transposition_date="")
    assert r["status"] == "pending"
    assert r["in_eu_27"] is True


def test_transposition_non_eu_country_flagged():
    r = _call(check_member_state_transposition,
              country_iso="UK", transposition_date="")
    assert r["in_eu_27"] is False


# ── misclassification forecaster ───────────────────────────────────────

def test_misclassification_spain_workers_high_exposure():
    r = _call(forecast_misclassification_risk,
              operator_name="Glovo ES", member_state_iso="ES",
              workers_at_risk=10000,
              avg_monthly_revenue_per_worker_eur=1800,
              months_of_exposure=24)
    assert r["fines_eur"]["central"] > 0
    assert r["estimated_back_pay_eur"] > 0
    assert r["regulator"].startswith("ITSS")


def test_misclassification_unknown_ms_returns_error():
    r = _call(forecast_misclassification_risk,
              operator_name="X", member_state_iso="ZZ",
              workers_at_risk=100,
              avg_monthly_revenue_per_worker_eur=1500,
              months_of_exposure=12)
    assert "error" in r


# ── audit pack ─────────────────────────────────────────────────────────

def test_audit_pack_has_11_sections():
    r = _call(prepare_eu_platform_audit_pack,
              operator_name="Wolt EU", operator_country="FI",
              workers_engaged=15000,
              member_states_active=["FI", "SE", "DE", "PL", "EE"])
    assert len(r["evidence_sections"]) == 11
    assert any("Art 6" in s["section"] for s in r["evidence_sections"])
    assert "FI" in r["member_states_active"]


# ── attestation + HMAC ────────────────────────────────────────────────

def test_attestation_chain():
    r = _call(check_employment_status_presumption,
              worker_name="K", member_state_iso="DE", indicators_present=[])
    assert "sig" in r and "ts" in r
    assert r["issuer"] == "meok-eu-platform-worker-mcp"
    assert r["version"] == "1.0.0"


def test_attestation_hmac_signs_when_secret_set(monkeypatch):
    monkeypatch.setattr(server_mod, "_HMAC_SECRET", "test-secret-key")
    r = _call(check_employment_status_presumption,
              worker_name="K", member_state_iso="DE",
              indicators_present=["remuneration_ceiling"])
    # Should not be the "unsigned" placeholder
    assert r["sig"] != "unsigned-no-key-configured"
    # And should be a 64-char hex digest (sha256)
    assert len(r["sig"]) == 64
    int(r["sig"], 16)  # raises if not hex


def test_attestation_unsigned_when_no_secret(monkeypatch):
    monkeypatch.setattr(server_mod, "_HMAC_SECRET", "")
    r = _call(check_employment_status_presumption,
              worker_name="K", member_state_iso="DE", indicators_present=[])
    assert r["sig"] == "unsigned-no-key-configured"


# ── regulatory-table integrity ─────────────────────────────────────────

def test_control_indicators_has_5_anchors():
    assert len(CONTROL_INDICATORS) == 5


def test_eu_27_table_size():
    assert len(EU_27) == 27


def test_known_precursors_include_ley_rider():
    assert "ES" in KNOWN_NATIONAL_PRECURSORS
    assert KNOWN_NATIONAL_PRECURSORS["ES"]["presumption_threshold"] == 1


def test_misclassification_table_covers_top_8_ms():
    for c in ["ES", "IT", "FR", "DE", "NL", "PT", "BE", "PL"]:
        assert c in MISCLASSIFICATION_FINE_RANGES_EUR


def test_transposition_deadline_is_dec_2_2026():
    assert TRANSPOSITION_DEADLINE.isoformat() == "2026-12-02"


def test_prohibited_categories_block_emotional_state():
    assert "emotional_or_psychological_state" in PROHIBITED_DATA_CATEGORIES


def test_consultation_triggers_include_pay_algo():
    assert "pay_algorithm_modified" in ALGORITHMIC_CHANGE_CONSULTATION_TRIGGERS


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
