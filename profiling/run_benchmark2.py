import cProfile, pstats, sys
sys.path.insert(0, '/root/Projeto Pangeia')
from pangeia.simulation import Simulation
from pangeia.config import SimulationConfig

cfg = SimulationConfig.default()
cfg.world.initial_population = 300
cfg.world.seed = 42
sim = Simulation(cfg)

prof = cProfile.Profile()
prof.enable()
for _ in range(10):
    sim.step()
prof.disable()

prof.dump_stats('/root/Projeto Pangeia/profiling/tick_profile_after.prof')

with open('/root/Projeto Pangeia/profiling/tick_profile_after.txt', 'w') as f:
    ps = pstats.Stats(prof, stream=f)
    ps.sort_stats('cumtime')
    ps.print_stats(30)
    f.write("\n\n=== By ncalls ===\n")
    ps.sort_stats('ncalls')
    ps.print_stats(20)
