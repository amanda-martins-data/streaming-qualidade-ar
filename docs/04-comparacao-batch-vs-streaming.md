# 04. Comparacao Batch vs Streaming

## Mesma linha de base, dois modelos

`latency_model.py` reaproveita a constante de volume real do
[Projeto 10](https://github.com/amanda-martins-data/capacity-planning-qualidade-ar) -
360 leituras/dia (3 cidades x 5 poluentes x 24 leituras/dia) - para
que a comparacao parta do mesmo cenario real em ambos os modelos, em
vez de numeros inventados para parecer favoraveis a um lado.
`test_baseline_matches_project_10` garante que essa constante nunca
diverge silenciosamente entre os dois projetos.

## Resultado

| Modelo | Pior caso de latencia | Fonte do numero |
|---|---|---|
| Batch (Projeto 04, real) | 24 horas | uma execucao diaria - uma leitura que chega logo apos a execucao espera quase um dia inteiro |
| Streaming (proposto) | ~3 segundos | valor tipico de referencia de sistemas de streaming gerenciados, nao medido em cluster real |

Fator de melhoria no pior caso: ordens de grandeza (`test_improvement_factor_is_large`
verifica que o fator excede 1000x, sem fixar um numero exato que
dependeria de infraestrutura nao provisionada).

## Por que o numero do batch nao depende do volume

`batch_latency()` nao usa `readings_per_day` no calculo - o gargalo
de latencia do modelo batch e a **frequencia de execucao** (uma vez
por dia), nao o volume processado por execucao. Processar 360 ou
36.000 leituras na mesma execucao diaria nao muda o pior caso de
latencia - so mudaria o tempo de execucao em si, que e exatamente o
que o [Projeto 10](https://github.com/amanda-martins-data/capacity-planning-qualidade-ar)
ja modelou e testou separadamente.

## Por que isso nao significa "trocar tudo para streaming"

O [Blueprint (Projeto 09)](https://github.com/amanda-martins-data/blueprint-arquitetura-corporativa)
definiu RN3 (dashboard aceita ate 1 hora de latencia) como requisito
real de negocio - e batch, com execucao horaria (nao diaria, como no
Projeto 04 atual, mas o mesmo modelo), ja atende isso com folga. A
melhoria de latencia de streaming e real e mensuravel, mas so vale a
complexidade operacional adicional (particionamento, schema
registry, consumer lag, os tres documentos anteriores) quando um
requisito de negocio concreto exigir algo que batch nao entrega -
exatamente o raciocinio do [ADR 0010](https://github.com/amanda-martins-data/adr-arquitetura-dados/blob/main/decisions/0010-batch-vs-streaming-proxima-evolucao.md).

## Custo (nao modelado em codigo, registrado aqui)

Diferente da comparacao de latencia, uma comparacao de custo real
exigiria precos de Kafka gerenciado (ex.: MSK, Confluent Cloud) ou
Kinesis contra o custo real ja calculado no
[Projeto 10](https://github.com/amanda-martins-data/capacity-planning-qualidade-ar)
($14,60/mes na linha de base) - isso nao foi modelado em codigo
neste projeto porque dependeria de escolher um provedor especifico
sem nenhuma decisao de infraestrutura real por tras. Fica registrado
como proximo passo explicito, nao como lacuna escondida: o dia em
que um dos gatilhos do ADR 0010 se tornar real, esse seria o
primeiro numero a calcular antes de qualquer implementacao.
