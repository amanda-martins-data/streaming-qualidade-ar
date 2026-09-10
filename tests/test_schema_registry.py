"""
Testes de schema_registry.py - 100% offline. Cobre os tres modos de
compatibilidade (backward, forward, full) com casos que deveriam
passar e casos que deveriam ser rejeitados.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from schema_registry import (
    Field,
    Schema,
    SchemaRegistry,
    check_backward_compatible,
    check_forward_compatible,
    check_full_compatible,
)


def make_schema(version: int, *fields: Field) -> Schema:
    return Schema(version=version, fields=list(fields))


def test_adding_optional_field_with_default_is_backward_compatible():
    old = make_schema(1, Field("sensor_id", "string", required=True))
    new = make_schema(
        2,
        Field("sensor_id", "string", required=True),
        Field("unidade", "string", required=True, default="ug/m3", has_default=True),
    )

    result = check_backward_compatible(old, new)

    assert result.compatible is True


def test_adding_required_field_without_default_breaks_backward_compatibility():
    old = make_schema(1, Field("sensor_id", "string", required=True))
    new = make_schema(
        2,
        Field("sensor_id", "string", required=True),
        Field("unidade", "string", required=True),  # sem default
    )

    result = check_backward_compatible(old, new)

    assert result.compatible is False
    assert "unidade" in result.reasons[0]


def test_removing_field_is_forward_compatible():
    """Remover um campo e seguro para forward: o leitor antigo so
    olha os campos que conhece, entao um campo a menos nao quebra
    nada - mas o campo removido precisa nao ser obrigatorio no schema
    antigo tambem, senao o proprio schema antigo ja teria exigido
    algo que nao existe mais."""
    old = make_schema(
        1,
        Field("sensor_id", "string", required=True),
        Field("nota_interna", "string", required=False),
    )
    new = make_schema(2, Field("sensor_id", "string", required=True))

    result = check_forward_compatible(old, new)

    assert result.compatible is True


def test_removing_required_field_breaks_forward_compatibility():
    old = make_schema(
        1,
        Field("sensor_id", "string", required=True),
        Field("poluente", "string", required=True),
    )
    new = make_schema(2, Field("sensor_id", "string", required=True))

    result = check_forward_compatible(old, new)

    assert result.compatible is False
    assert "poluente" in result.reasons[0]


def test_full_compatible_requires_both_backward_and_forward():
    old = make_schema(
        1,
        Field("sensor_id", "string", required=True),
        Field("poluente", "string", required=True),
    )
    # remove campo obrigatorio (quebra forward) E adiciona campo obrigatorio sem default (quebra backward)
    new = make_schema(
        2,
        Field("sensor_id", "string", required=True),
        Field("unidade", "string", required=True),
    )

    result = check_full_compatible(old, new)

    assert result.compatible is False
    assert len(result.reasons) == 2  # um motivo de cada lado


def test_registry_accepts_compatible_evolution():
    registry = SchemaRegistry(compatibility_mode="full")
    registry.register([Field("sensor_id", "string", required=True)])

    v2 = registry.register(
        [
            Field("sensor_id", "string", required=True),
            Field("unidade", "string", required=True, default="ug/m3", has_default=True),
        ]
    )

    assert v2.version == 2
    assert registry.latest().version == 2


def test_registry_rejects_incompatible_evolution():
    registry = SchemaRegistry(compatibility_mode="full")
    registry.register(
        [
            Field("sensor_id", "string", required=True),
            Field("poluente", "string", required=True),
        ]
    )

    with pytest.raises(ValueError, match="incompativel"):
        registry.register([Field("sensor_id", "string", required=True)])


def test_registry_keeps_old_version_after_rejected_change():
    """Uma tentativa de registro rejeitada nao deveria deixar o
    registry em estado inconsistente - a ultima versao valida
    continua sendo a mesma de antes da tentativa."""
    registry = SchemaRegistry(compatibility_mode="full")
    registry.register(
        [
            Field("sensor_id", "string", required=True),
            Field("poluente", "string", required=True),
        ]
    )

    try:
        registry.register([Field("sensor_id", "string", required=True)])
    except ValueError:
        pass

    assert registry.latest().version == 1
    assert len(registry.all_versions()) == 1


def test_registry_invalid_compatibility_mode_raises():
    with pytest.raises(ValueError):
        SchemaRegistry(compatibility_mode="nonsense")


def test_get_specific_version():
    registry = SchemaRegistry(compatibility_mode="backward")
    registry.register([Field("sensor_id", "string", required=True)])
    registry.register(
        [
            Field("sensor_id", "string", required=True),
            Field("extra", "string", required=True, default="x", has_default=True),
        ]
    )

    v1 = registry.get(1)

    assert v1.version == 1
    assert len(v1.fields) == 1
