# 03. Particionamento e Ordenacao

## Por que particionar por municipio_id (ou cidade)

Seguindo o mesmo raciocinio ja usado no isolamento multi-tenant do
[Projeto 09](https://github.com/amanda-martins-data/blueprint-arquitetura-corporativa/blob/main/04-modelo-fisico.md#decisao-nova-isolamento-fisico-de-dados-entre-municipios)
e no particionamento fisico do
[Projeto 04](https://github.com/amanda-martins-data/iac-pipeline-cloud-qualidade-ar),
o `EventBus` deste projeto particiona eventos pela mesma chave que
faz sentido de negocio: cidade/municipio. `partition_for_key()` usa
hash da chave para determinar a particao - a mesma chave sempre cai
na mesma particao, o que da uma garantia importante: **ordem
preservada por cidade**, mesmo que a ordem global entre cidades
diferentes nao seja garantida (e nao precisa ser - um alerta de
qualidade do ar de Sao Paulo nao depende da ordem relativa a um
evento do Rio de Janeiro).

`test_same_key_always_goes_to_same_partition` e
`test_order_is_preserved_within_a_partition` confirmam essa garantia
diretamente.

## Entrega at-least-once, nao exactly-once

O modelo implementado aqui e **at-least-once**: um evento pode ser
entregue mais de uma vez (se o consumidor falhar entre processar e
confirmar), mas nunca e perdido silenciosamente. `poll()` nunca
avanca o offset sozinho - so `ack()` faz isso, e chamar `poll()`
repetidamente sem `ack()` sempre retorna os mesmos eventos
(`test_poll_without_ack_returns_same_events_again`).

A alternativa, exactly-once, exigiria coordenacao transacional entre
o broker e o consumidor (ex.: escrita idempotente no destino) - fora
do escopo desta prova de conceito, mas o padrao de design (offset
separado do processamento, avancado so apos confirmacao explicita) e
o mesmo usado por sistemas reais para viabilizar exactly-once quando
necessario.

## Lag como sinal operacional

`lag()` retorna quantos eventos um consumidor ainda nao confirmou
numa particao - a metrica que, em um sistema real (Kafka Consumer
Lag, CloudWatch para Kinesis), dispara alerta quando um consumidor
fica para tras da taxa de producao. `test_lag_reflects_unacked_events`
confirma o calculo com um cenario simples: publicar 3, confirmar 2,
lag fica 1.

## Multiplos consumidores independentes

`test_two_consumers_have_independent_offsets` confirma que dois
consumidores diferentes (ex.: um alimentando o dashboard, outro
alimentando o historico de longo prazo) avancam seus proprios
offsets sem interferir um no outro - a base que viabiliza o gatilho
3 do [ADR 0010](https://github.com/amanda-martins-data/adr-arquitetura-dados/blob/main/decisions/0010-batch-vs-streaming-proxima-evolucao.md)
("multiplos consumidores downstream precisando reagir ao mesmo
evento").

## O que fica fora desta prova de conceito

- Replicacao entre brokers (tolerancia a falha de infraestrutura).
- Rebalanceamento automatico de particoes entre multiplas instancias
  de um mesmo consumer group.
- Persistencia em disco - tudo aqui vive em memoria, apagado ao
  final do processo.

Estes tres itens sao exatamente o que um cluster Kafka/Kinesis real
adiciona sobre esta prova de conceito - a decisao de adotar a
infraestrutura de verdade continua dependendo dos gatilhos do
[ADR 0010](https://github.com/amanda-martins-data/adr-arquitetura-dados/blob/main/decisions/0010-batch-vs-streaming-proxima-evolucao.md).
