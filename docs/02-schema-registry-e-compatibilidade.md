# 02. Schema Registry e Compatibilidade

## O mesmo problema do ADR 0009, agora com codigo

O [ADR 0009](https://github.com/amanda-martins-data/adr-arquitetura-dados/blob/main/decisions/0009-estrategia-evolucao-de-schema-em-parquet.md)
decidiu, em prosa, que mudancas aditivas de schema (nova coluna)
seriam toleradas automaticamente, enquanto mudancas destrutivas
(remocao, troca de tipo) exigiriam versionamento explicito. Este
projeto implementa exatamente essa logica como codigo verificavel,
usando as definicoes padrao da industria de compatibilidade backward
e forward.

## As tres perguntas que o registry responde

**Backward**: dados escritos com o schema antigo podem ser lidos com
o schema novo? Quebra quando o schema novo adiciona um campo
obrigatorio sem valor default - o dado antigo simplesmente nao tem
esse campo. `test_adding_required_field_without_default_breaks_backward_compatibility`
confirma isso.

**Forward**: dados escritos com o schema novo podem ser lidos com o
schema antigo? Quebra quando um campo obrigatorio do schema antigo e
removido - o leitor antigo espera aquele campo e nao vai
encontra-lo. `test_removing_required_field_breaks_forward_compatibility`
confirma isso.

**Full**: as duas ao mesmo tempo - o modo mais rigoroso, exigido
quando ha multiplos consumidores independentes lendo o mesmo topico
(exatamente o gatilho 3 do ADR 0010: "multiplos consumidores
downstream").

## Por que full compatibility e o modo certo para este cenario

Com um unico pipeline lendo seus proprios dados (como o Projeto 04
hoje), backward compatibility sozinha bastaria. Mas um sistema de
streaming de verdade tipicamente tem multiplos consumidores
independentes (ex.: o dashboard, o alerta de emergencia, o pipeline
de relatorio mensal) lendo o mesmo topico de eventos - cada um pode
estar rodando uma versao diferente do codigo consumidor em um dado
momento. Nesse cenario, so full compatibility garante que nenhum
consumidor quebre, independente de qual versao de schema ele
espera.

## O registry rejeita, nao so avisa

`SchemaRegistry.register()` lanca `ValueError` quando uma mudanca
quebra o modo de compatibilidade configurado - nao registra a versao
incompativel e depois avisa, **recusa o registro**.
`test_registry_keeps_old_version_after_rejected_change` confirma que
uma tentativa rejeitada nao deixa o registry em estado inconsistente:
a ultima versao valida continua sendo a mesma de antes da tentativa.

Isso espelha como um schema registry real (ex.: Confluent Schema
Registry) se comporta em modo estrito: a mudanca de schema
incompativel e barrada no momento do registro, nao descoberta depois
em produção quando um consumidor ja quebrou.

## Exemplo

```python
from schema_registry import SchemaRegistry, Field

registry = SchemaRegistry(compatibility_mode="full")

registry.register([
    Field("sensor_id", "string", required=True),
    Field("poluente", "string", required=True),
])

# aditiva com default - aceita
registry.register([
    Field("sensor_id", "string", required=True),
    Field("poluente", "string", required=True),
    Field("unidade", "string", required=True, default="ug/m3", has_default=True),
])

# remove campo obrigatorio - rejeitada
registry.register([
    Field("sensor_id", "string", required=True),
])
# ValueError: schema v3 incompativel (full): campo obrigatorio
# 'poluente' do schema v2 foi removido no schema v3 - leitores
# antigos quebrariam
```
