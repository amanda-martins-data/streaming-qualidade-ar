"""
schema_registry.py
--------------------
Registro de schemas para eventos de qualidade do ar, com verificacao
de compatibilidade backward e forward - o mesmo problema ja discutido
em prosa no ADR 0009 do repositorio de arquitetura (estrategia de
evolucao de schema em Parquet), agora implementado e testado de
verdade para o cenario de streaming.

Definicoes (padrao da industria, ex.: Confluent Schema Registry):
- BACKWARD compativel: dados escritos com o schema ANTIGO podem ser
  lidos com o schema NOVO. Seguro adicionar campo opcional (com
  default); inseguro adicionar campo obrigatorio sem default (o
  dado antigo nao tem esse campo).
- FORWARD compativel: dados escritos com o schema NOVO podem ser
  lidos com o schema ANTIGO. Seguro adicionar campo (o leitor antigo
  ignora o que nao conhece); inseguro remover um campo que o schema
  antigo espera como obrigatorio.
- FULL compativel: backward E forward ao mesmo tempo - o requisito
  mais rigoroso, tipicamente o que se exige de eventos de producao
  com multiplos consumidores independentes.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Field:
    name: str
    type: str
    required: bool
    default: object = None
    has_default: bool = False


@dataclass
class Schema:
    version: int
    fields: list[Field] = field(default_factory=list)

    def field_map(self) -> dict[str, Field]:
        return {f.name: f for f in self.fields}


@dataclass
class CompatibilityResult:
    compatible: bool
    mode: str
    reasons: list[str] = field(default_factory=list)


def check_backward_compatible(old: Schema, new: Schema) -> CompatibilityResult:
    """Dados do schema `old` devem poder ser lidos pelo schema `new`.
    Quebra quando o schema novo adiciona um campo obrigatorio sem
    default - dados antigos nao tem esse campo para preencher."""
    old_fields = old.field_map()
    reasons = []

    for name, f in new.field_map().items():
        if name not in old_fields and f.required and not f.has_default:
            reasons.append(
                f"campo novo obrigatorio '{name}' sem valor default - "
                f"dados escritos com o schema v{old.version} nao teriam esse campo"
            )

    return CompatibilityResult(compatible=not reasons, mode="backward", reasons=reasons)


def check_forward_compatible(old: Schema, new: Schema) -> CompatibilityResult:
    """Dados do schema `new` devem poder ser lidos pelo schema `old`.
    Quebra quando um campo obrigatorio do schema antigo e removido no
    schema novo - o leitor antigo espera aquele campo e nao vai
    encontra-lo."""
    new_fields = new.field_map()
    reasons = []

    for name, f in old.field_map().items():
        if f.required and name not in new_fields:
            reasons.append(
                f"campo obrigatorio '{name}' do schema v{old.version} foi removido "
                f"no schema v{new.version} - leitores antigos quebrariam"
            )

    return CompatibilityResult(compatible=not reasons, mode="forward", reasons=reasons)


def check_full_compatible(old: Schema, new: Schema) -> CompatibilityResult:
    """Compatibilidade total: backward E forward simultaneamente."""
    backward = check_backward_compatible(old, new)
    forward = check_forward_compatible(old, new)
    reasons = backward.reasons + forward.reasons

    return CompatibilityResult(compatible=backward.compatible and forward.compatible, mode="full", reasons=reasons)


class SchemaRegistry:
    """Guarda o historico de versoes de um schema e decide se uma
    nova versao pode ser registrada, segundo o modo de
    compatibilidade escolhido (backward, forward ou full)."""

    CHECKERS = {
        "backward": check_backward_compatible,
        "forward": check_forward_compatible,
        "full": check_full_compatible,
    }

    def __init__(self, compatibility_mode: str = "full") -> None:
        if compatibility_mode not in self.CHECKERS:
            raise ValueError(f"modo de compatibilidade invalido: {compatibility_mode!r}")
        self.compatibility_mode = compatibility_mode
        self._versions: list[Schema] = []

    def register(self, fields: list[Field]) -> Schema:
        """Registra uma nova versao de schema. Lanca ValueError se a
        nova versao quebrar o modo de compatibilidade configurado com
        a versao mais recente ja registrada."""
        next_version = len(self._versions) + 1
        candidate = Schema(version=next_version, fields=fields)

        if self._versions:
            checker = self.CHECKERS[self.compatibility_mode]
            result = checker(self._versions[-1], candidate)
            if not result.compatible:
                raise ValueError(
                    f"schema v{next_version} incompativel ({self.compatibility_mode}): "
                    + "; ".join(result.reasons)
                )

        self._versions.append(candidate)
        return candidate

    def latest(self) -> Schema | None:
        return self._versions[-1] if self._versions else None

    def get(self, version: int) -> Schema:
        for s in self._versions:
            if s.version == version:
                return s
        raise KeyError(f"versao {version} nao encontrada")

    def all_versions(self) -> list[Schema]:
        return list(self._versions)
