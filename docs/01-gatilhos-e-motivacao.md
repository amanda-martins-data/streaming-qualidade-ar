# 01. Gatilhos e Motivacao

## Este projeto existe para responder a uma pergunta ja levantada

O [ADR 0010](https://github.com/amanda-martins-data/adr-arquitetura-dados/blob/main/decisions/0010-batch-vs-streaming-proxima-evolucao.md)
do repositorio de arquitetura decidiu **permanecer em batch** para o
pipeline real do Projeto 04, registrando explicitamente os tres
gatilhos que justificariam migrar para streaming - sem implementar
nenhum deles, porque nenhum se aplicava ao cenario real na epoca.

Este projeto nao contradiz aquele ADR - ele prepara a resposta para
quando um desses gatilhos aparecer, com uma prova de conceito real e
testada, em vez de deixar a decisao inteiramente para o futuro sem
nenhum trabalho de base feito.

## Os tres gatilhos, revisitados

O ADR 0010 listava:

1. Um caso de uso de alerta com SLA de latencia menor que o menor
   intervalo de batch pratico.
2. Volume de eventos justificando o custo fixo de um cluster de
   streaming.
3. Multiplos consumidores downstream precisando reagir ao mesmo
   evento em tempo real.

O [Blueprint (Projeto 09)](https://github.com/amanda-martins-data/blueprint-arquitetura-corporativa)
ja continha um requisito de negocio (RN3) aceitando ate 1 hora de
latencia para o dashboard - dentro do que batch resolve. Mas o
proprio blueprint reconhece, em
[06-requisitos-nao-funcionais.md](https://github.com/amanda-martins-data/blueprint-arquitetura-corporativa/blob/main/06-requisitos-nao-funcionais.md),
que um cenario de **alerta de emergencia** (pico de poluicao exigindo
aviso imediato) teria requisito de latencia muito mais agressivo que
RN3 - esse e o gatilho 1 se tornando concreto.

## O que este projeto prova, com codigo real

- **Schema registry com compatibilidade verificada**
  ([docs/02](02-schema-registry-e-compatibilidade.md)): o mesmo
  problema de evolucao de schema do
  [ADR 0009](https://github.com/amanda-martins-data/adr-arquitetura-dados/blob/main/decisions/0009-estrategia-evolucao-de-schema-em-parquet.md),
  agora implementado e testado, nao so discutido em prosa.
- **Particionamento e ordem, com entrega at-least-once**
  ([docs/03](03-particionamento-e-ordenacao.md)): as garantias
  centrais que tornariam um sistema de streaming real confiavel,
  simuladas em memoria e testadas.
- **Comparacao de latencia com numeros da linha de base real**
  ([docs/04](04-comparacao-batch-vs-streaming.md)): nao uma
  comparacao abstrata "streaming e mais rapido", mas um numero
  concreto usando o mesmo volume de 360 leituras/dia ja usado e
  testado no [Projeto 10](https://github.com/amanda-martins-data/capacity-planning-qualidade-ar).

## O que isto nao e

Isto nao e um cluster Kafka ou Kinesis provisionado - e uma prova de
conceito em Python puro que implementa e testa as garantias que
importariam (particionamento, ordem, entrega, compatibilidade de
schema), sem a infraestrutura de fato. A decisao de migrar de
verdade continua sendo do ADR 0010: **so quando um dos tres gatilhos
se tornar real**, nao antes.
