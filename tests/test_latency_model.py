"""
Testes de latency_model.py - 100% offline.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from latency_model import (
    BASELINE_READINGS_PER_DAY,
    batch_latency,
    latency_improvement_factor,
    streaming_latency,
)


def test_baseline_matches_project_10():
    """A linha de base deste projeto precisa ser identica a do
    Projeto 10 (capacity-planning-qualidade-ar) - 360 leituras/dia -
    para que a comparacao batch vs streaming parta do mesmo volume
    real em ambos os projetos."""
    assert BASELINE_READINGS_PER_DAY == 360


def test_batch_worst_case_is_about_24_hours():
    result = batch_latency()

    assert result.worst_case_latency_seconds == 24 * 60 * 60
    assert result.worst_case_latency_human == "24.0h"


def test_streaming_latency_is_in_seconds():
    result = streaming_latency()

    assert result.worst_case_latency_seconds < 60
    assert "s" in result.worst_case_latency_human


def test_streaming_is_faster_than_batch():
    batch = batch_latency()
    streaming = streaming_latency()

    assert streaming.worst_case_latency_seconds < batch.worst_case_latency_seconds


def test_improvement_factor_is_large():
    """Nao afirma um numero magico - so confirma que a melhoria e de
    ordens de grandeza, coerente com trocar um pior-caso de 24h por
    um de poucos segundos."""
    factor = latency_improvement_factor()

    assert factor > 1000


def test_human_readable_format_switches_units_correctly():
    from latency_model import LatencyComparison

    seconds_case = LatencyComparison("teste", 1, 30)
    minutes_case = LatencyComparison("teste", 1, 120)
    hours_case = LatencyComparison("teste", 1, 7200)

    assert seconds_case.worst_case_latency_human == "30s"
    assert minutes_case.worst_case_latency_human == "2.0min"
    assert hours_case.worst_case_latency_human == "2.0h"
