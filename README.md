# Bolsa Família — Projeto Pangeia

Simulação do programa Bolsa Família (PBF) como subsistema de política social
no [Projeto Pangeia](https://github.com/Yukio80/projeto-pangeia), um laboratório
de civilizações artificiais baseado em agentes autônomos.

## O que é

O PBF foi modelado como um programa de transferência condicionada de renda
dentro da simulação multiagente do Pangeia. Agentes com riqueza abaixo de um
limiar recebem benefícios periódicos, financiados por uma sobretaxa sobre os
agentes mais ricos. O programa exige contrapartidas (frequência escolar e
acompanhamento de saúde) e gradua os beneficiários após um período mínimo de
participação.

## Estrutura

```
pangeia/social_welfare/          # Subsistema PBF
├── __init__.py                  # SocialWelfareSystem + Beneficiary
└── config.py                    # SocialWelfareConfig + GraduationMode

scenarios/
├── run_bolsa_familia.py         # Harness de 5 cenários
└── gen_report.py                # Geração do relatório Markdown

scenario_outputs/                # Séries temporais CSV (5 cenários)
├── 1_baseline.csv
├── 2_padrao.csv
├── 3a_corte_abrupto.csv
├── 3b_corte_gradual.csv
└── 4_subfinanciado.csv

documents/
└── relatorio-bolsa-familia.md   # Relatório completo
```

## Integração no Pangeia

O subsistema toca os seguintes arquivos do núcleo:

| Arquivo | Mudança |
|---------|---------|
| `pangeia/config.py` | `SocialWelfareConfig` adicionado ao `SimulationConfig` |
| `pangeia/simulation.py` | `SocialWelfareSystem` instanciado e chamado no step |
| `pangeia/engine/simulation_worker.py` | `social_welfare` no snapshot de estado |
| `pangeia/api/state_reader.py` | Método `social_welfare()` + chave no summary |
| `pangeia/api/server.py` | Rota `GET /social-welfare` |

## Cenários

| # | Cenário | Descrição |
|---|---------|-----------|
| 1 | Baseline | Política desativada |
| 2 | PBF Padrão | Gradual com taper 0.1 |
| 3a | Corte Abrupto | Graduação sem transição |
| 3b | Corte Gradual | Taper 0.3 |
| 4 | Subfinanciado | Surcharge 1% (vs 5%) |

## Como rodar

```bash
cd projeto-pangeia
PYTHONPATH=. python scenarios/run_bolsa_familia.py
```

## Resultados principais

- **128 famílias graduadas** (64% da população) em todos os cenários com PBF
- **Pobreza eliminada**: de 38% para 0%
- **Gini reduzido**: de 0.4747 para ~0.064
- **Déficit fiscal**: ~-10.000 unidades (benefício supera arrecadação da sobretaxa)
- **Robusto**: mesmo com 1% de alíquota, mantém 128 graduações

## Distribuição inicial de riqueza

A população de 200 agentes segue uma distribuição exponencial com cauda longa:

| Classe | Faixa | % |
|--------|-------|---|
| Miserável | < 20 | 25% |
| Pobre | 20–80 | 31% |
| Classe média | 80–200 | 28% |
| Média alta | 200–500 | 14% |
| Elite | > 500 | 2% |

Gini inicial: 0.543 (comparável ao Gini real do Brasil: ~0.53).

## Limitações

- Agentes não sofrem choques econômicos negativos — não há recaída na pobreza
- Baixa variabilidade transversal de riqueza após muitos ticks
- Modelo unidimensional de riqueza (sem renda, ativos, dívida)
