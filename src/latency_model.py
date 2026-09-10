"""
latency_model.py
------------------
Compara a latencia entre a arquitetura batch real (Projeto 04,
Lambda diaria) e a arquitetura de streaming proposta aqui, usando a
mesma linha de base de volume do Projeto 10
(capacity-planning-qualidade-ar): 360 leituras/dia = 3 cidades x 5
poluentes x 24 leituras/dia.

Nao inventa numeros novos - reaproveita a constante de linha de base
ja usada e testada no Projeto 10, para que a comparacao entre batch
e streaming parta do mesmo volume real em ambos os casos.
"""

from __future__ import annotations

from dataclasses import dataclass

BASELINE_READINGS_PER_DAY = 360  # identico ao Projeto 10

# Batch (Projeto 04 real): execucao unica diaria - pior caso de
# latencia e uma leitura que chega logo apos a execucao do dia
# anterior, esperando quase 24h pela proxima execucao.
BATCH_EXECUTIONS_PER_DAY = 1
BATCH_WORST_CASE_LATENCY_SECONDS = 24 * 60 * 60 / BATCH_EXECUTIONS_PER_DAY

# Streaming (este projeto): latencia e o tempo entre publish() e o
# consumidor confirmar o evento - dominado por overhead de rede e
# processamento, no modelo de referencia usamos um valor tipico de
# sistemas de streaming gerenciados (nao medido em cluster real, ja
# que nao ha infraestrutura provisionada).
STREAMING_TYPICAL_LATENCY_SECONDS = 3.0


@dataclass
class LatencyComparison:
    scenario: str
    readings_per_day: int
    worst_case_latency_seconds: float

    @property
    def worst_case_latency_human(self) -> str:
        seconds = self.worst_case_latency_seconds
        if seconds < 60:
            return f"{seconds:.0f}s"
        if seconds < 3600:
            return f"{seconds / 60:.1f}min"
        return f"{seconds / 3600:.1f}h"


def batch_latency(readings_per_day: int = BASELINE_READINGS_PER_DAY) -> LatencyComparison:
    """Pior caso de latencia do modelo batch: independe do volume de
    leituras (o gargalo e a frequencia de execucao, nao o volume
    processado por execucao) - por isso `readings_per_day` nao entra
    no calculo, mas fica no resultado para contexto."""
    return LatencyComparison(
        scenario="batch (Projeto 04)",
        readings_per_day=readings_per_day,
        worst_case_latency_seconds=BATCH_WORST_CASE_LATENCY_SECONDS,
    )


def streaming_latency(readings_per_day: int = BASELINE_READINGS_PER_DAY) -> LatencyComparison:
    """Latencia tipica do modelo de streaming: tambem nao depende do
    volume neste modelo simplificado - um sistema de streaming bem
    dimensionado mantem latencia por evento aproximadamente constante
    independente do volume total (o volume afeta throughput agregado,
    nao a latencia de um evento individual)."""
    return LatencyComparison(
        scenario="streaming (proposto)",
        readings_per_day=readings_per_day,
        worst_case_latency_seconds=STREAMING_TYPICAL_LATENCY_SECONDS,
    )


def latency_improvement_factor(readings_per_day: int = BASELINE_READINGS_PER_DAY) -> float:
    """Quantas vezes mais rapido o streaming e, no pior caso, em
    relacao ao batch - um numero unico para resumir a comparacao."""
    batch = batch_latency(readings_per_day)
    streaming = streaming_latency(readings_per_day)
    return batch.worst_case_latency_seconds / streaming.worst_case_latency_seconds
