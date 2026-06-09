# Resultados de Benchmark - Otimizacao de Performance

## Metodologia
- 300 agentes, 10 ticks, seed=42
- `cProfile` capturando cumulative time
- Medido em `profiling/tick_profile_baseline.txt` (antes) e `profiling/tick_profile_after.txt` (depois)

## Resultados

| Metrica | Antes | Depois | Ganho |
|---------|-------|--------|-------|
| Total function calls | 297.375 | 224.448 | -25% |
| `step()` cumulative | 0.786s | 0.646s | -18% |
| ticks/sec (10 ticks) | 23.7 | 24.5 | +3.4% |

> Nota: ticks/sec com 10 ticks inclui overhead de inicializacao. O ganho real no hot loop
> do step() e de ~18%. Para populacoes maiores (1000+), o ganho e mais significativo
> pois eliminamos O(n²) nas chamadas de summary/researchable.

## Top 5 Funcoes Otimizadas

### 1. `perceive()` — 2.1x mais rapido
- **Antes**: 0.170s (chamava economy.summary() + governance.summary() + resources.as_dict() por agente)
- **Depois**: 0.080s (usa cache pre-computado por tick)
- **Fix**: `_expensive_cache` em `simulation.step()` pre-computa summaries 1x/tick

### 2. `economy.summary()` — eliminado do hot path
- **Antes**: 0.058s, 2280 chamadas (1x por agente por tick via perceive)
- **Depois**: 0 chamadas no hot loop

### 3. `governance.summary()` — eliminado do hot path
- **Antes**: 0.028s, 2280 chamadas
- **Depois**: 0 chamadas no hot loop

### 4. `technology.can_research()` — eliminado do hot path
- **Antes**: 8043 chamadas (recalculava a cada research step)
- **Depois**: Cache `_researchable_cache`, invalidado apenas quando uma tech e descoberta

### 5. `as_dict()` agent state — mantido (nao otimizado)
- **Antes**: 0.055s, 2280 chamadas
- **Depois**: 0.062s (aumento marginal)
- **Nota**: necessario para cada perceive(), nao trivial de cachear

## Problemas Encontrados e Corrigidos Durante a Otimizacao

### `rng.shuffle()` catastrófico
- `self.rng.shuffle(others)` no `socializing` causou 295.233 chamadas a `_randbelow_with_getrandbits`
- Isso resultou em 1.514s total (pior que baseline de 0.779s)
- **Fix**: Substituido por `self.rng.sample(others, min(10, len(others)))` — 501 chamadas vs 983 shuffles
- **Licao**: `shuffle()` e O(n) com custo alto de `_randbelow`. So usar quando necessario.

## Impacto das Correcoes de Memoria (deque)

(Medido separadamente — sem impacto significativo em ticks/sec com 300 agentes)

- `Memory.short_term` e `long_term`: `deque(maxlen=N)` — crescimento O(1) amorticado
- `trim_reputation()` a cada 10 ticks — overhead < 0.001s
- `AgentState.trim_reputation()` em `step()` — overhead negligible

## Conclusao
- Perceive caching foi a otimizacao mais efetiva (elimina O(n²))
- Researchable cache elimina 8043 calls/tick de can_research
- shuffle -> sample foi correcao necessaria apos regression
- Para 1000+ agentes, o ganho deve ser > 2x pois O(n²) domina
