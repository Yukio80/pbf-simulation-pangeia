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

prof.dump_stats('/root/Projeto Pangeia/profiling/tick_profile_baseline.prof')

import pstats
with open('/root/Projeto Pangeia/profiling/tick_profile.txt', 'w') as f:
    ps = pstats.Stats(prof, stream=f)
    ps.sort_stats('cumtime')
    ps.print_stats(30)

import time
cfg2 = SimulationConfig.default()
cfg2.world.initial_population = 300
cfg2.world.seed = 42
sim2 = Simulation(cfg2)
start = time.time()
for _ in range(10):
    sim2.step()
elapsed = time.time() - start
print(f"BASELINE: 10 ticks with 300 agents: {elapsed:.3f}s ({10/elapsed:.1f} ticks/s)")
