#!/usr/bin/env python3
"""Projeto Pangeia — Laboratório de Civilizações Artificiais.

Usage:
  python main.py              # Run API server
  python main.py --cli        # Run in CLI simulation mode
  python main.py --ticks N    # Run N ticks in CLI mode
"""

import argparse
import sys
import time

from pangeia.simulation import Simulation
from pangeia.config import SimulationConfig


def run_cli(config: SimulationConfig = None, ticks: int = 100):
    if config is None:
        config = SimulationConfig.default()
    from pangeia.persistence.config import PersistenceConfig
    config.persistence = PersistenceConfig.from_env()
    sim = Simulation(config)

    print("=" * 60)
    print("PROJETO PANGEIA — Civilização Artificial Emergente")
    print("=" * 60)
    print(f"População inicial: {config.world.initial_population}")
    print(f"Territórios: {len(sim.world.state.territories)}")
    print(f"Sementes aleatórias: {config.world.seed}")
    print("=" * 60)

    start_time = time.time()

    for i in range(ticks):
        snapshot = sim.step()
        if i % 10 == 0 or i == ticks - 1:
            _print_tick(sim, i + 1)

    elapsed = time.time() - start_time
    print("=" * 60)
    print(f"Simulação concluída: {ticks} ticks em {elapsed:.2f}s")
    print(f"({ticks / max(0.001, elapsed):.1f} ticks/s)")
    print("=" * 60)
    _print_final_summary(sim)


def _print_tick(sim, tick):
    metrics = sim.metrics.history[-1] if sim.metrics.history else None
    if metrics:
        tech_era = sim.technology.get_era()[:4] if sim.technology else "...."
        print(f"Tick {tick:5d} | "
              f"Pop: {metrics.alive}/{metrics.population} | "
              f"Era: {tech_era:>4} | "
              f"Polar: {metrics.polarization:.2f} | "
              f"Feliz: {metrics.collective_happiness:.2f} | "
              f"Estab: {metrics.stability:.2f}"
              )
    else:
        econ = sim.economy.summary()
        print(f"Tick {tick:5d} | "
              f"Empresas: {econ['companies']} | "
              f"Recursos: {sim.world.state.global_resources.as_dict()}"
              )


def _print_final_summary(sim):
    s = sim.summary()
    print("\nRESUMO FINAL")
    print("-" * 40)
    print(f"Agentes: {s['agents']['total']} ({s['agents']['alive']} vivos)")
    print(f"Distribuicao: {s['agents']['by_class']}")
    print(f"Economia: PIB={s['economy']['indicators']['gdp']:.1f}, "
          f"Desigualdade={s['economy']['indicators']['inequality']:.3f}")
    print(f"Governanca: {s['governance']['government']['type']}, "
          f"Estabilidade={s['governance']['government']['stability']:.2f}")
    print(f"Tecnologia: era {s['technology']['era']}, "
          f"{s['technology']['discovered']}/{s['technology']['total_technologies']} descobertas")
    print(f"Eventos: {sum(1 for e in sim.world.state.events if e['type'] == 'event_start')}")
    print(f"Religioes: {s['culture']['religion']['religions']}, "
          f"Ideologias: {s['culture']['ideologies']['total_ideologies']}, "
          f"Faccoes: {len(s['diplomacy']['factions'])}")
    classes_str = ", ".join(f"{c['name']}={c['members']}" for c in s['stratification']['classes'])
    print(f"Classes: {classes_str}")
    print(f"Indice Civilizacao: "
          f"{s['civilization']['age']}, "
          f"Tech={s['civilization']['technology']:.2f}, "
          f"Estab={s['civilization']['stability']:.2f}, "
          f"Cultura={s['civilization']['culture_complexity']:.2f}")


def run_api(host: str = "0.0.0.0", port: int = 8000):
    import uvicorn
    print(f"🌍 Projeto Pangeia API rodando em http://{host}:{port}")
    host_display = host if host != "0.0.0.0" else "localhost"
    print(f"Documentacao: http://{host_display}:{port}/docs")
    uvicorn.run("pangeia.api.server:app", host=host, port=port, reload=False)


def main():
    parser = argparse.ArgumentParser(
        description="Projeto Pangeia — Laboratório de Civilizações Artificiais"
    )
    parser.add_argument("--cli", action="store_true", help="Modo CLI")
    parser.add_argument("--ticks", type=int, default=100, help="Número de ticks")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host da API")
    parser.add_argument("--port", type=int, default=8000, help="Porta da API")
    parser.add_argument("--population", type=int, default=500, help="População inicial")

    args = parser.parse_args()

    cfg = SimulationConfig.default()
    cfg.world.initial_population = args.population
    from pangeia.persistence.config import PersistenceConfig
    cfg.persistence = PersistenceConfig.from_env()

    if args.cli:
        run_cli(config=cfg, ticks=args.ticks)
    else:
        run_api(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
