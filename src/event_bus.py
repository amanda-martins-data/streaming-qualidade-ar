"""
event_bus.py
-------------
Barramento de eventos em memoria, simulando as garantias centrais de
um sistema real (Kafka/Kinesis) que seriam usadas para o caso de
alerta em tempo real ja discutido no ADR 0010 do repositorio de
arquitetura: particionamento por chave, ordem preservada dentro de
uma particao, e entrega at-least-once (uma mensagem so avanca depois
de confirmada - se o consumidor falhar antes de confirmar, a mesma
mensagem e entregue de novo).

Isto nao substitui um cluster Kafka real - e uma prova de conceito
que implementa e testa as garantias que importam, sem a
infraestrutura de fato.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Event:
    key: str
    payload: dict


class EventBus:
    def __init__(self, num_partitions: int) -> None:
        if num_partitions < 1:
            raise ValueError("num_partitions deve ser >= 1")
        self.num_partitions = num_partitions
        self._partitions: dict[int, list[Event]] = {i: [] for i in range(num_partitions)}
        self._consumer_offsets: dict[str, dict[int, int]] = {}

    def partition_for_key(self, key: str) -> int:
        """Determina a particao de uma chave via hash - a mesma chave
        sempre cai na mesma particao, o que garante ordem por chave
        (ex.: todas as leituras de um mesmo municipio_id ficam na
        mesma particao, na ordem em que foram publicadas)."""
        return hash(key) % self.num_partitions

    def publish(self, key: str, payload: dict) -> int:
        partition = self.partition_for_key(key)
        self._partitions[partition].append(Event(key=key, payload=payload))
        return partition

    def subscribe(self, consumer_id: str) -> None:
        """Registra um consumidor, comecando do offset 0 em todas as
        particoes - um consumidor novo le o topico inteiro desde o
        inicio, como no Kafka com um novo consumer group."""
        self._consumer_offsets[consumer_id] = {i: 0 for i in range(self.num_partitions)}

    def poll(self, consumer_id: str, partition: int, max_events: int = 10) -> list[Event]:
        """Le eventos a partir do offset atual do consumidor NESSA
        particao - nao avanca o offset. Chamar poll() duas vezes sem
        ack() entre as chamadas retorna os mesmos eventos - e assim
        que a redelivery at-least-once acontece."""
        if consumer_id not in self._consumer_offsets:
            raise KeyError(f"consumidor '{consumer_id}' nao inscrito")

        offset = self._consumer_offsets[consumer_id][partition]
        return self._partitions[partition][offset : offset + max_events]

    def ack(self, consumer_id: str, partition: int, count: int) -> None:
        """Confirma o processamento de `count` eventos, avancando o
        offset - so depois do ack() e que uma proxima chamada a
        poll() deixa de retornar os eventos ja processados."""
        if consumer_id not in self._consumer_offsets:
            raise KeyError(f"consumidor '{consumer_id}' nao inscrito")

        self._consumer_offsets[consumer_id][partition] += count

    def lag(self, consumer_id: str, partition: int) -> int:
        """Quantos eventos ainda nao foram confirmados por esse
        consumidor nessa particao - a metrica que, em um sistema
        real, dispara alerta quando um consumidor fica para tras."""
        total = len(self._partitions[partition])
        offset = self._consumer_offsets[consumer_id][partition]
        return total - offset
