"""
Testes de event_bus.py - 100% offline. Cobre particionamento por
chave, ordem preservada, e redelivery at-least-once.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from event_bus import EventBus


def test_same_key_always_goes_to_same_partition():
    bus = EventBus(num_partitions=8)

    p1 = bus.publish("SP", {"valor": 1})
    p2 = bus.publish("SP", {"valor": 2})
    p3 = bus.publish("SP", {"valor": 3})

    assert p1 == p2 == p3


def test_order_is_preserved_within_a_partition():
    bus = EventBus(num_partitions=1)  # forca tudo na mesma particao
    bus.subscribe("consumer-1")

    bus.publish("SP", {"ordem": 1})
    bus.publish("SP", {"ordem": 2})
    bus.publish("SP", {"ordem": 3})

    events = bus.poll("consumer-1", partition=0, max_events=10)

    assert [e.payload["ordem"] for e in events] == [1, 2, 3]


def test_poll_without_ack_returns_same_events_again():
    """A garantia central de entrega at-least-once: se o consumidor
    nao confirmar, a proxima leitura traz os mesmos eventos de novo -
    simulando um consumidor que processou mas falhou antes do ack."""
    bus = EventBus(num_partitions=1)
    bus.subscribe("consumer-1")
    bus.publish("SP", {"valor": 1})

    first_read = bus.poll("consumer-1", partition=0)
    second_read = bus.poll("consumer-1", partition=0)

    assert first_read == second_read


def test_ack_advances_offset_so_events_are_not_repeated():
    bus = EventBus(num_partitions=1)
    bus.subscribe("consumer-1")
    bus.publish("SP", {"valor": 1})
    bus.publish("SP", {"valor": 2})

    first_read = bus.poll("consumer-1", partition=0, max_events=1)
    bus.ack("consumer-1", partition=0, count=len(first_read))
    second_read = bus.poll("consumer-1", partition=0, max_events=1)

    assert first_read[0].payload["valor"] == 1
    assert second_read[0].payload["valor"] == 2


def test_lag_reflects_unacked_events():
    bus = EventBus(num_partitions=1)
    bus.subscribe("consumer-1")
    bus.publish("SP", {"valor": 1})
    bus.publish("SP", {"valor": 2})
    bus.publish("SP", {"valor": 3})

    assert bus.lag("consumer-1", partition=0) == 3

    events = bus.poll("consumer-1", partition=0, max_events=2)
    bus.ack("consumer-1", partition=0, count=len(events))

    assert bus.lag("consumer-1", partition=0) == 1


def test_different_keys_can_land_on_different_partitions():
    """Nao garantido para todo par de chaves (depende do hash), mas
    com particoes e chaves suficientes, esperamos ver mais de uma
    particao em uso - se isso falhar, o particionamento nao esta de
    fato distribuindo carga."""
    bus = EventBus(num_partitions=8)
    keys = [f"cidade-{i}" for i in range(20)]

    partitions_used = {bus.publish(k, {}) for k in keys}

    assert len(partitions_used) > 1


def test_poll_unsubscribed_consumer_raises():
    bus = EventBus(num_partitions=1)

    with pytest.raises(KeyError):
        bus.poll("nunca-inscrito", partition=0)


def test_num_partitions_must_be_positive():
    with pytest.raises(ValueError):
        EventBus(num_partitions=0)


def test_two_consumers_have_independent_offsets():
    """Dois consumidores diferentes (ex.: um grava no dashboard,
    outro grava no historico) leem o mesmo topico de forma
    independente - o offset de um nao afeta o do outro."""
    bus = EventBus(num_partitions=1)
    bus.subscribe("dashboard-consumer")
    bus.subscribe("historico-consumer")
    bus.publish("SP", {"valor": 1})

    bus.ack("dashboard-consumer", partition=0, count=1)

    assert bus.lag("dashboard-consumer", partition=0) == 0
    assert bus.lag("historico-consumer", partition=0) == 1
