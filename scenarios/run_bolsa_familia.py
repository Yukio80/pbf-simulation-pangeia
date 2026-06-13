"""Harness para rodar os 6 cenários de comparação do subsistema Bolsa Família
no Pangeia e exportar séries temporais para CSV.

Cenários:
  1) Baseline         - social_welfare desativado
  2) PBF padrão       - parâmetros calibrados
  3a) Corte abrupto   - graduação sem transição
  3b) Corte gradual   - graduação com taper
  4)  Subfinanciado   - tax_surcharge insuficiente
  5)  Capital returns - elite com retorno proporcional ao patrimônio (1%/tick)
"""

import csv
import os
import random

from pangeia.config import SimulationConfig
from pangeia.simulation import Simulation

N_TICKS = 500
OUTPUT_DIR = "scenario_outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def distribute_initial_wealth(sim, cfg):
    agents = list(sim.agents.values())
    rng = random.Random(cfg.world.seed + 999)
    mean = 120.0; floor = 5.0
    for agent in agents:
        raw = rng.expovariate(1.0 / mean)
        w = floor + raw
        if rng.random() < 0.05: w *= 1.5 + rng.random() * 2.0
        if rng.random() < 0.15: w = floor + rng.random() * 15.0
        agent.state.wealth = w
    if hasattr(sim, "agent_array") and sim.agent_array is not None:
        sim.agent_array.sync_from_agents(sim.agents)


def apply_capital_returns(sim):
    """Aplica retorno proporcional ao patrimônio por faixa de riqueza.
    Wealth >= 500 (elite): 1%/tick  (~12,7% a.a. se tick ~ mês)
    Wealth 200-499 (média-alta): 0,3%/tick (~3,7% a.a.)
    Wealth < 200: 0%
    """
    for agent in sim.agents.values():
        if not agent.state.is_alive or agent.state.wealth <= 0:
            continue
        w = agent.state.wealth
        if w >= 500:
            rate = 0.01
        elif w >= 200:
            rate = 0.003
        else:
            continue
        agent.state.wealth += w * rate


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

    elif scenario in ("5a_capital_return_5pct", "5b_capital_return_1pct"):
        cfg.social_welfare.graduation_mode = "gradual"
        cfg.social_welfare.graduation_transition_band = 0.1
        if scenario == "5b_capital_return_1pct":
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
    "5a_capital_return_5pct",
    "5b_capital_return_1pct",
]


def run_scenario(scenario: str) -> list[dict]:
    cfg = build_config(scenario)
    sim = Simulation(cfg)
    distribute_initial_wealth(sim, cfg)
    sim.stratification.assign_classes(sim.agents)

    has_capital_return = scenario.startswith("5")

    rows = []
    for tick in range(N_TICKS):
        sim.step()

        if has_capital_return:
            apply_capital_returns(sim)

        sw = sim.social_welfare.summary()

        alive = [a for a in sim.agents.values() if a.state.is_alive]
        ws = sorted(a.state.wealth for a in alive) if alive else [0]
        n_rich = sum(1 for w in ws if w > 180) if alive else 0
        gini = _gini(ws) if len(ws) > 1 else 0.0

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
            "n_acima_180": n_rich,
            "gini_real": round(gini, 4),
            "avg_wealth": round(sum(ws) / len(ws), 1) if ws else 0,
        }
        rows.append(row)

    return rows


def _gini(values):
    if not values or sum(values) == 0:
        return 0.0
    s = sorted(values)
    n = len(s)
    return (2 * sum((i + 1) * v for i, v in enumerate(s))) / (n * sum(s)) - (n + 1) / n


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


def main():
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
            first = rows[0]
            print(
                f"  Gini: {last['gini']:.4f} (start: {first['gini']:.4f})  "
                f"Pobreza: {last['poverty_rate']:.2%}  "
                f"Graduados: {last['graduated_total']}  "
                f"Coletado: {last['total_surtax_collected']:,.0f}  "
                f"Fundo: {last['fund_balance']:.0f}  "
                f"n>180: {last['n_acima_180']}  "
                f"Wealth avg: {last['avg_wealth']:.0f}"
            )
        print()

    print("Todos os cenários concluídos. CSVs em:", OUTPUT_DIR)


if __name__ == "__main__":
    main()
