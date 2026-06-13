"""Harness para rodar os 5 cenários de comparação do subsistema Bolsa Família
no Pangeia e exportar séries temporais para CSV.

Cenários:
  1) Baseline        - social_welfare desativado
  2) PBF padrão      - parâmetros calibrados
  3a) Corte abrupto  - graduação sem transição
  3b) Corte gradual  - graduação com taper
  4)  Subfinanciado  - tax_surcharge insuficiente
"""

import csv
import os
import random

from pangeia.config import SimulationConfig
from pangeia.simulation import Simulation

# ----------------------------------------------------------------------
# Configuração geral
# ----------------------------------------------------------------------

N_TICKS = 500
OUTPUT_DIR = "scenario_outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ----------------------------------------------------------------------
# Distribuição inicial de riqueza
# ----------------------------------------------------------------------


def distribute_initial_wealth(sim: Simulation, cfg: SimulationConfig) -> None:
    """Substitui a riqueza uniforme dos agentes por uma distribuição
    exponencial (Pareto-like) para gerar pobres, classe média e elite.

    A distribuição segue uma exponencial com média 'mean' e piso 'floor',
    mais um punhado de agentes muito ricos (cauda longa).
    """
    agents = list(sim.agents.values())
    seed = cfg.world.seed
    rng = random.Random(seed + 999)

    mean = 120.0
    floor = 5.0

    for agent in agents:
        raw = rng.expovariate(1.0 / mean)
        wealth = floor + raw

        # cauda longa: ~5% ganham um boost extra (elite)
        if rng.random() < 0.05:
            wealth *= 1.5 + rng.random() * 2.0
        # ~15% ficam na miséria (reforço da cauda inferior)
        if rng.random() < 0.15:
            wealth = floor + rng.random() * 15.0

        agent.state.wealth = wealth

    # Sincroniza o AgentArray (se existir)
    if hasattr(sim, "agent_array") and sim.agent_array is not None:
        sim.agent_array.sync_from_agents(sim.agents)


# ----------------------------------------------------------------------
# Definição dos cenários
# ----------------------------------------------------------------------


def build_config(scenario: str) -> SimulationConfig:
    cfg = SimulationConfig()
    cfg.world.initial_population = 200

    if scenario == "1_baseline":
        cfg.social_welfare.enabled = False
        return cfg

    cfg.social_welfare.enabled = True
    cfg.social_welfare.eligibility_threshold = 90.0
    cfg.social_welfare.benefit_per_capita = 12.0
    cfg.social_welfare.funding_tax_surcharge = 0.05
    cfg.social_welfare.conditionalities_enabled = True
    cfg.social_welfare.graduation_grace_ticks = 30

    if scenario == "2_padrao":
        cfg.social_welfare.graduation_mode = "gradual"
        cfg.social_welfare.graduation_transition_band = 0.1

    elif scenario == "3a_corte_abrupto":
        cfg.social_welfare.graduation_mode = "abrupt"

    elif scenario == "3b_corte_gradual":
        cfg.social_welfare.graduation_mode = "gradual"
        cfg.social_welfare.graduation_transition_band = 0.3

    elif scenario == "4_subfinanciado":
        cfg.social_welfare.graduation_mode = "gradual"
        cfg.social_welfare.graduation_transition_band = 0.1
        cfg.social_welfare.funding_tax_surcharge = 0.01

    else:
        raise ValueError(f"Cenário desconhecido: {scenario}")

    return cfg


SCENARIOS = [
    "1_baseline",
    "2_padrao",
    "3a_corte_abrupto",
    "3b_corte_gradual",
    "4_subfinanciado",
]

# ----------------------------------------------------------------------
# Execução e coleta de métricas
# ----------------------------------------------------------------------


def run_scenario(scenario: str) -> list[dict]:
    cfg = build_config(scenario)
    sim = Simulation(cfg)

    # Distribuição realista de riqueza inicial
    distribute_initial_wealth(sim, cfg)

    # Re-classificar estratificação com base na nova riqueza
    sim.stratification.assign_classes(sim.agents)

    rows = []
    for tick in range(N_TICKS):
        sim.step()

        sw = sim.social_welfare.summary()

        row = {
            "tick": tick,
            "scenario": scenario,
            "enabled": int(cfg.social_welfare.enabled),
            "gini": sw["gini_before"],
            "gini_post_transfer": sw["gini_after"],
            "poverty_rate": sw["poverty_rate_before"],
            "poverty_rate_post_transfer": sw["poverty_rate_after"],
            "beneficiaries": sw["active_beneficiaries"],
            "coverage_ratio": sw["coverage_ratio"],
            "graduated_total": sw["graduated_count"],
            "fund_balance": sw["fund_balance"],
            "total_transfers": sw["total_disbursed"],
            "total_surtax_collected": sw["total_collected"],
            "benefit_per_capita": sw["benefit_per_capita"],
            "eligibility_threshold": sw["eligibility_threshold"],
        }
        rows.append(row)

    return rows


def export_csv(scenario: str, rows: list[dict]) -> str:
    path = os.path.join(OUTPUT_DIR, f"{scenario}.csv")
    if not rows:
        return path
    fieldnames = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return path


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------


def main():
    # Quick sanity check on wealth distribution
    print("Verificando distribuição inicial de riqueza...")
    test_cfg = build_config("2_padrao")
    test_sim = Simulation(test_cfg)
    distribute_initial_wealth(test_sim, test_cfg)
    wealths = sorted(a.state.wealth for a in test_sim.agents.values())
    print(f"  Amostra: {[f'{w:.0f}' for w in wealths[:10]]} ... {[f'{w:.0f}' for w in wealths[-10:]]}")
    print(f"  Min: {wealths[0]:.1f}  Max: {wealths[-1]:.1f}  Mediana: {wealths[len(wealths)//2]:.1f}")
    poor = sum(1 for w in wealths if w < 90)
    print(f"  Abaixo do limiar (90): {poor}/{len(wealths)} ({poor/len(wealths)*100:.0f}%)")
    rich = sum(1 for w in wealths if w > 300)
    print(f"  Acima de 300: {rich}/{len(wealths)} ({rich/len(wealths)*100:.0f}%)")
    print()

    for scenario in SCENARIOS:
        print(f"Rodando cenário: {scenario} ({N_TICKS} ticks)...")
        rows = run_scenario(scenario)
        path = export_csv(scenario, rows)
        print(f"  -> exportado para {path}")

        if rows:
            last = rows[-1]
            print(
                f"  Gini: {last['gini']:.4f} → {last['gini_post_transfer']:.4f}  "
                f"Pobreza: {last['poverty_rate']:.2%} → {last['poverty_rate_post_transfer']:.2%}  "
                f"Beneficiários: {last['beneficiaries']}  "
                f"Graduados: {last['graduated_total']}  "
                f"Saldo do fundo: {last['fund_balance']:.1f}"
            )
        print()

    print("Todos os cenários concluídos. CSVs em:", OUTPUT_DIR)


if __name__ == "__main__":
    main()
