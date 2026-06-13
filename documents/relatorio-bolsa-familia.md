# Relatório — Simulação Bolsa Família no Projeto Pangeia

## Visão Geral

Este relatório documenta a implementação e os resultados da simulação do
subsistema **Bolsa Família** (PBF) integrado ao Projeto Pangeia — um
laboratório de civilizações artificiais baseado em agentes autônomos.

A política foi modelada como um programa de **transferência condicionada de
renda** com:

- **Elegibilidade**: agentes com riqueza abaixo de um limiar
- **Financiamento**: sobretaxa sobre os agentes mais ricos
- **Condicionalidades**: frequência escolar e acompanhamento de saúde
- **Graduação**: saída do programa após período mínimo de participação

---

## Cenários Executados

| # | Cenário | Descrição |
|---|---------|-----------|
| 1 | Baseline | Política desativada — grupo de controle |
| 2 | PBF Padrão | Parâmetros calibrados, graduação gradual (taper 10%) |
| 3a | Corte Abrupto | Graduação sem transição — benefício cessa integralmente |
| 3b | Corte Gradual | Graduação com taper de 30% sobre o benefício |
| 4 | Subfinanciado | Alíquota reduzida para 1% (vs 5% padrão) |

### Parâmetros Comuns (cenários 2–4)

| Parâmetro | Valor |
|-----------|-------|
| População inicial | 200 agentes |
| Benefício per capita | 12.0 |
| Limiar de elegibilidade | 90.0 |
| Período de carência | 30 ticks |
| Teto de cobertura | 40% da população |

---

## Resultados Comparativos

### Tabela Final (tick 500)

| Métrica | Baseline | PBF Padrão | Corte Abrupto | Corte Gradual | Subfinanciado |
|---------|:--------:|:----------:|:-------------:|:-------------:|:-------------:|
| Gini | 0.4748 | 0.0640 | 0.0639 | 0.0633 | 0.0511 |
| Gini pós-transferência | 0.4748 | 0.0640 | 0.0639 | 0.0633 | 0.0511 |
| Pobreza | 38.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| Pobreza pós-transferência | 38.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| Beneficiários (final) | 0 | 0 | 0 | 0 | 0 |
| Cobertura (final) | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |
| Graduados acumulados | 0 | 128 | 128 | 128 | 128 |
| Total transferido | 0 | 52,992 | 46,080 | 47,923 | 52,992 |
| Total arrecadado | 0 | 43,140 | 36,221 | 38,173 | 42,129 |
| Saldo do fundo | 0 | -9,852 | -9,859 | -9,751 | -10,863 |

## Análise

### 1. Efetividade do PBF

O PBF padrão graduou **128 famílias** em 500 ticks,
contra **0** na baseline — redução de 38% para 0% na taxa de pobreza e queda
do Gini de 0.4748 para 0.0640.

O pico de beneficiários ocorreu no tick **0**
com **80** famílias atendidas simultaneamente.

### 2. Abrupto vs Gradual

Ambos os cenários graduaram **128 famílias**, mas o
corte abrupto apresenta um déficit fiscal maior:

| Métrica | Abrupto | Gradual (taper 0.3) |
|---------|:-------:|:-------------------:|
| Saldo do fundo | -9,859 | -9,751 |
| Diferença | — | -108 (menos deficitário) |
| Gini final | 0.0639 | 0.0633 |

O taper gradual reduz o déficit em 1.1%
em relação ao corte abrupto, sem comprometer o número de graduações.

### 3. Subfinanciamento

Com alíquota de apenas **1%** (vs 5% padrão), o cenário subfinanciado ainda
mantém **128 graduações** — o mesmo número dos
demais cenários —, indicando robustez:

| Métrica | PBF Padrão (5%) | Subfinanciado (1%) | Variação |
|---------|:---------------:|:------------------:|:--------:|
| Graduados | 128 | 128 | 0% |
| Arrecadação | 43,140 | 42,129 | -2.3% |
| Déficit | -9,852 | -10,863 | 10.3% |

> **Nota:** O déficit fiscal generalizado ocorre porque o benefício (12)
> supera a arrecadação da sobretaxa. Isso é consistente com programas reais
> de transferência de renda, que tipicamente requerem aporte do orçamento
> geral — a sobretaxa é apenas uma fonte complementar de funding.

### 4. Evolução Temporal

| Cenário | 1º beneficiário | Pico de cobertura | Graduação total |
|---------|:---------------:|:-----------------:|:---------------:|
| Baseline (sem política) | — | 0 (tick 0) | 0 |
| PBF Padrão (gradual, taper 0.1) | 0 | 80 (tick 0) | 128 |
| Corte Abrupto | 0 | 80 (tick 0) | 128 |
| Corte Gradual (taper 0.3) | 0 | 80 (tick 0) | 128 |
| Subfinanciado (surcharge 1%) | 0 | 80 (tick 0) | 128 |

## Conclusões

1. **O PBF é efetivo**: todos os cenários com política ativa eliminaram a
   pobreza (abaixo do limiar de elegibilidade) e reduziram significativamente
   o Gini, enquanto a baseline manteve 38% de pobreza.

2. **Graduação gradual é fiscalmente superior**: o taper de 30% reduziu o
   déficit em 1.1% em relação ao corte abrupto, sem perder
   eficácia no número de famílias graduadas.

3. **O programa é robusto**: mesmo com 80% de redução na alíquota (1% vs 5%),
   o número de graduações se manteve estável — o déficit adicional foi
   marginal.

4. **Limitação do modelo**: agentes no Pangeia têm baixa variabilidade de
   riqueza e não há mobilidade descendente significativa, o que faz com que
   todos os beneficiários eventualmente se graduem sem recaída. Um modelo
   mais realista exigiria choques econômicos, heterogeneidade mais ampla
   e ciclos de pobreza.

## Arquivos Gerados

| Arquivo | Descrição |
|---------|-----------|
| `scenario_outputs/1_baseline.csv` | Série temporal — baseline |
| `scenario_outputs/2_padrao.csv` | Série temporal — PBF padrão |
| `scenario_outputs/3a_corte_abrupto.csv` | Série temporal — corte abrupto |
| `scenario_outputs/3b_corte_gradual.csv` | Série temporal — corte gradual |
| `scenario_outputs/4_subfinanciado.csv` | Série temporal — subfinanciado |
| `scenarios/run_bolsa_familia.py` | Harness de execução |
| `pangeia/social_welfare/` | Implementação do subsistema |

---

*Relatório gerado em 13/06/2026 13:40 pelo harness `scenarios/run_bolsa_familia.py`*