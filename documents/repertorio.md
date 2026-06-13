# Repertório — Bolsa Família no Projeto Pangeia

## 1. Implementação do subsistema

### `pangeia/social_welfare/config.py`
Define a configuração do programa: benefício, elegibilidade, surcharge,
condicionalidades, modo e período de graduação.

- `SocialWelfareConfig` — dataclass com 13 parâmetros
- `GraduationMode` — enum `abrupt` / `gradual`

### `pangeia/social_welfare/__init__.py`
Núcleo da política social.

- `Beneficiary` — dataclass de cada agente beneficiado
- `SocialWelfareSystem` — classe principal com:
  - `step()` — ciclo tick: elegibilidade → arrecadação → distribuição →
    condicionalidades → graduação → métricas
  - `_assess_eligibility()` — seleciona os mais pobres até o teto
  - `_collect_funds()` — surcharge sobre riqueza > 2× threshold
  - `_distribute_benefits()` — crédito do benefício (com taper gradual)
  - `_check_conditionalities()` — frequência escolar e saúde
  - `_process_graduation()` — saída após carência
  - `_record_metrics()` — Gini pré/pós, pobreza, cobertura
  - `summary()` — dicionário serializável para API/snapshot

## 2. Integração no núcleo do Pangeia

### `pangeia/config.py` (linha 6, 81)
Importa `SocialWelfareConfig` e o inclui como campo de `SimulationConfig`.

### `pangeia/simulation.py` (linhas 32, 192-193, 407)
Importa, instancia e chama `social_welfare.step(self, tick)` a cada tick.

### `pangeia/engine/simulation_worker.py` (linha 53)
Adiciona `social_welfare` ao `_build_state_snapshot()`.

### `pangeia/api/state_reader.py` (linhas 58, 104-105)
Adiciona chave no `summary()` e método `social_welfare()`.

### `pangeia/api/server.py` (linhas 244-245)
Rota `GET /social-welfare`.

## 3. Experimentos

### `scenarios/run_bolsa_familia.py`
Harness que executa 5 cenários (500 ticks cada, 200 agentes) e exporta CSVs.

Fluxo:
1. `build_config()` — configura parâmetros por cenário
2. `distribute_initial_wealth()` — distribuição exponencial com pobres/miseráveis
3. `Simulation(cfg)` → `sim.step()` × 500
4. Coleta métricas por tick → CSV

### `scenarios/gen_report.py`
Gera `documents/relatorio-bolsa-familia.md` a partir dos CSVs.

## 4. Dados gerados

### `scenario_outputs/*.csv`
5 arquivos CSV com 501 linhas cada (cabeçalho + 500 ticks).

Colunas: `tick, scenario, enabled, gini, gini_post_transfer, poverty_rate,
poverty_rate_post_transfer, beneficiaries, coverage_ratio, graduated_total,
fund_balance, total_transfers, total_surtax_collected, benefit_per_capita,
eligibility_threshold`

### `documents/relatorio-bolsa-familia.md`
Relatório final com tabelas, análise e conclusões.

### `/root/documents/relatorio-bolsa-familia.md`
Cópia do relatório.

## 5. Diagrama de fluxo

```
build_config()
     │
     ▼
Simulation(cfg)
     │
     ▼
distribute_initial_wealth()
     │  (expovariate: 25% miserável, 31% pobre, 28% média, 14% média alta, 2% elite)
     ▼
for tick in 0..499:
     │
     ├─ sim.step()
     │     │
     │     ├─ economia, governança, ... (núcleo Pangeia)
     │     │
     │     └─ social_welfare.step()
     │           │
     │           ├─ enabled? → retorna se False
     │           ├─ _assess_eligibility()  → novos beneficiários
     │           ├─ _collect_funds()       → surcharge nos ricos
     │           ├─ _distribute_benefits() → crédito nos pobres
     │           ├─ _check_conditionalities()
     │           ├─ _process_graduation()  → saída após carência
     │           └─ _record_metrics()     → Gini, pobreza, cobertura
     │
     └─ coleta métricas → append no CSV
```

## 6. Resumo dos resultados

| Métrica | Baseline | Com PBF |
|---------|:--------:|:-------:|
| Gini | 0.4747 | ~0.064 |
| Pobreza | 38% | 0% |
| Graduados | 0 | 128 |
| Déficit fiscal | 0 | ~-10.000 |

Os 5 cenários produziram resultados quase idênticos em graduações (128),
variando apenas no saldo do fundo (-9.828 a -10.982).
