# Arquitetura Orientada a Eventos (Streaming)

Prova de conceito real e testada de uma arquitetura de streaming para
qualidade do ar - schema registry com compatibilidade backward/
forward verificada, event bus com particionamento e entrega
at-least-once, e um modelo de latencia comparando batch (Projeto 04
real) contra streaming, usando o mesmo volume real ja usado no
[Projeto 10](https://github.com/amanda-martins-data/capacity-planning-qualidade-ar).

Projeto 12 de uma serie documentando minha transicao de Analista de
Dados para Arquitetura de Dados - veja o [perfil
completo](https://github.com/amanda-martins-data).

## Por que este projeto

O [ADR 0010](https://github.com/amanda-martins-data/adr-arquitetura-dados/blob/main/decisions/0010-batch-vs-streaming-proxima-evolucao.md)
decidiu permanecer em batch para o Projeto 04, registrando tres
gatilhos que justificariam migrar - sem implementar nenhum, porque
nenhum se aplicava na epoca. Este projeto prepara a resposta para
quando um desses gatilhos aparecer: nao um cluster Kafka provisionado
(fora do escopo sem infraestrutura real), mas as garantias que
importariam - particionamento, ordem, entrega, compatibilidade de
schema - implementadas e testadas de verdade.

## O achado central

Batch (Projeto 04 real, execucao diaria) tem pior caso de latencia
de 24 horas; o modelo de streaming proposto, ~3 segundos - uma
melhoria de ordens de grandeza, calculada sobre a mesma linha de
base de 360 leituras/dia ja testada no
[Projeto 10](https://github.com/amanda-martins-data/capacity-planning-qualidade-ar).
Mas o RN3 do [Blueprint (Projeto 09)](https://github.com/amanda-martins-data/blueprint-arquitetura-corporativa)
so exige ate 1 hora - batch ja atende isso. Detalhes completos em
[docs/04-comparacao-batch-vs-streaming.md](docs/04-comparacao-batch-vs-streaming.md).

## Estrutura

```
.
├── docs/
│   ├── 01-gatilhos-e-motivacao.md              # por que este projeto, ligado ao ADR 0010
│   ├── 02-schema-registry-e-compatibilidade.md # backward/forward/full, ligado ao ADR 0009
│   ├── 03-particionamento-e-ordenacao.md       # garantias do event bus
│   └── 04-comparacao-batch-vs-streaming.md     # latencia com numeros reais
├── src/
│   ├── schema_registry.py   # compatibilidade de schema verificada
│   ├── event_bus.py         # particionamento, ordem, entrega at-least-once
│   └── latency_model.py     # comparacao batch vs streaming
└── tests/
    ├── test_schema_registry.py
    ├── test_event_bus.py
    └── test_latency_model.py
```

## Como rodar

```bash
pip install -r requirements.txt

# rodar os 25 testes
python -m pytest tests/ -v

# comparar latencia
python -c "
from src.latency_model import batch_latency, streaming_latency
print('Batch:', batch_latency().worst_case_latency_human)
print('Streaming:', streaming_latency().worst_case_latency_human)
"
```

## Validacao

**25/25 testes passando**, incluindo:
- Compatibilidade backward/forward/full verificada com casos que
  deveriam passar e casos que deveriam ser rejeitados.
- Registry mantém estado consistente apos uma tentativa de registro
  rejeitada.
- Mesma chave sempre cai na mesma particao (ordem preservada por
  cidade).
- Entrega at-least-once: `poll()` sem `ack()` retorna os mesmos
  eventos.
- Consumer lag calculado corretamente.
- Linha de base de latencia (360 leituras/dia) identica a do
  Projeto 10, verificada por teste dedicado para nunca divergir
  silenciosamente entre os dois projetos.

## O que isto nao e

Nao ha cluster Kafka ou Kinesis provisionado - tudo roda em memoria,
em um unico processo Python. O valor deste projeto esta nas
garantias implementadas e testadas (compatibilidade de schema,
particionamento, entrega), nao em uma infraestrutura de producao. A
decisao de adotar streaming de verdade continua dependendo dos
gatilhos concretos do [ADR 0010](https://github.com/amanda-martins-data/adr-arquitetura-dados/blob/main/decisions/0010-batch-vs-streaming-proxima-evolucao.md).
