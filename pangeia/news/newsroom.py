from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from pangeia.simulation import Simulation
    from pangeia.core.agent import Agent


@dataclass
class NewsArticle:
    id: str
    tick: int
    headline: str
    summary: str
    category: str
    severity: str
    source_type: Optional[str] = None
    source_id: Optional[str] = None
    related_agent_ids: List[str] = field(default_factory=list)
    related_entities: Dict[str, str] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "tick": self.tick,
            "headline": self.headline,
            "summary": self.summary,
            "category": self.category,
            "severity": self.severity,
            "source_type": self.source_type,
            "source_id": self.source_id,
            "related_agent_ids": self.related_agent_ids,
            "related_entities": self.related_entities,
        }


class NewsRoom:
    def __init__(self, rng: Optional[random.Random] = None):
        self.rng = rng or random.Random()
        self.articles: List[NewsArticle] = []
        self._last_economy = {}
        self._last_pop = 0
        self._last_tech_level = 0.0
        self._last_inequality = 0.5
        self._last_happiness = 0.5
        self._last_religion_count = 0
        self._last_ideology_count = 0
        self._last_company_count = 0
        self._article_counter = 0

    def _next_id(self) -> str:
        self._article_counter += 1
        return f"news_{self._article_counter}"

    def _publish(self, tick: int, headline: str, summary: str,
                 category: str, severity: str = "minor",
                 **kwargs) -> Optional[NewsArticle]:
        article = NewsArticle(
            id=self._next_id(),
            tick=tick,
            headline=headline,
            summary=summary,
            category=category,
            severity=severity,
            **kwargs,
        )
        self.articles.append(article)
        return article

    def tick(self, sim: Simulation):
        econ = sim.economy
        metrics = sim.metrics
        tick = sim.world.state.tick
        current = metrics.history[-1] if metrics.history else None
        prev = metrics.history[-2] if len(metrics.history) >= 2 else None

        if current is None:
            return

        if tick == 0:
            self._publish(tick,
                f"A Civilização Pangeia começa com {current.population} almas",
                f"{current.population} agentes artificiais despertam em um mundo virgem, "
                f"prontos para construir sociedade, cultura e tecnologia.",
                "society", "breaking",
            )
            self._seed_snapshot(econ, sim)
            return

        self._check_economy(econ, sim, tick)
        self._check_technology(sim, tick)
        self._check_culture(sim, tick)
        self._check_demographics(current, prev, sim, tick)
        self._check_random_events(sim, tick)
        self._check_milestones(current, sim, tick)

        if tick % 50 == 0 and tick > 0:
            self._digest(current, sim, tick)

    def _seed_snapshot(self, econ, sim):
        self._last_economy = {
            "gdp": econ.indicators.gdp,
            "trade_volume": econ.indicators.trade_volume,
            "productivity": econ.indicators.productivity,
        }
        self._last_pop = sim.world.state.tick
        self._last_tech_level = sim.technology.get_tech_level() if sim.technology else 0.0
        self._last_inequality = econ.indicators.inequality
        self._last_happiness = 0.5
        self._last_religion_count = len(sim.religion_system.religions)
        self._last_ideology_count = len(sim.ideology_system.ideologies)
        if hasattr(econ, 'market') and hasattr(econ.market, 'companies'):
            self._last_company_count = len(econ.market.companies)

    def _check_economy(self, econ, sim, tick):
        now = {
            "gdp": econ.indicators.gdp,
            "trade_volume": econ.indicators.trade_volume,
            "productivity": econ.indicators.productivity,
        }
        prev = self._last_economy
        if not prev:
            self._last_economy = now
            return

        gdp_pct = ((now["gdp"] - prev["gdp"]) / max(1, prev["gdp"])) * 100
        ineq = econ.indicators.inequality
        ineq_delta = ineq - self._last_inequality

        if gdp_pct > 15:
            self._publish(tick,
                f"Economia em disparada: PIB cresce {gdp_pct:.0f}% no tick {tick}",
                f"O produto interno bruto de Pangeia saltou de {prev['gdp']:.1f} para "
                f"{now['gdp']:.1f}, sinalizando um período de crescimento acelerado.",
                "economy", "major",
            )
        elif gdp_pct < -15:
            self._publish(tick,
                f"Recessão: PIB despenca {abs(gdp_pct):.0f}%",
                f"A economia contraiu abruptamente, com o PIB caindo para {now['gdp']:.1f}. "
                f"Agentes podem enfrentar tempos difíceis.",
                "economy", "major",
            )

        if ineq_delta > 0.1:
            self._publish(tick,
                f"Desigualdade atinge {ineq:.0%} — abismo social se aprofunda",
                f"A concentração de riqueza aumentou {ineq_delta:.0%} em um único tick, "
                f"sugerindo que os ricos estão ficando mais ricos enquanto outros estagnam.",
                "economy", "major",
            )
        elif ineq_delta < -0.1:
            self._publish(tick,
                f"Desigualdade cai para {ineq:.0%}: sinais de redistribuição",
                f"A diferença entre os agentes mais ricos e mais pobres diminuiu, "
                f"possivelmente devido a políticas econômicas ou mobilidade social.",
                "economy", "minor",
            )

        self._last_economy = now
        self._last_inequality = ineq

    def _check_technology(self, sim, tick):
        if not sim.technology:
            return
        level = sim.technology.get_tech_level()
        tech = sim.technology
        era = tech.get_era()

        if level - self._last_tech_level > 0.1:
            discovered = [t for t in tech.technologies.values()
                          if t.discovered and t.discovery_tick == tick]
            for t in discovered:
                self._publish(tick,
                    f"Descoberta: {t.name}",
                    f"Pesquisadores em Pangeia desenvolveram {t.name}, localizada na era "
                    f"{t.era}. {t.description}",
                    "technology", "major",
                    source_type="technology", source_id=t.name,
                )

        if era != self._get_era_name(self._last_tech_level, tech):
            self._publish(tick,
                f"Nova Era Tecnológica: {era}",
                f"Pangeia entra na era {era}, marcando um salto qualitativo na capacidade "
                f"tecnológica da civilização.",
                "technology", "breaking",
            )

        self._last_tech_level = level

    def _get_era_name(self, level, tech=None):
        if tech:
            return tech.get_era()
        if level < 0.2:
            return "Primordial"
        elif level < 0.4:
            return "Descoberta"
        elif level < 0.6:
            return "Expansão"
        elif level < 0.8:
            return "Iluminação"
        else:
            return "Transcendência"

    def _check_culture(self, sim, tick):
        rel_count = len(sim.religion_system.religions)
        ideo_count = len(sim.ideology_system.ideologies)

        if rel_count > self._last_religion_count:
            new_rels = [
                r for r in sim.religion_system.religions.values()
                if r.id not in getattr(self, '_seen_religions', set())
            ]
            if not hasattr(self, '_seen_religions'):
                self._seen_religions = set()
            for r in new_rels:
                self._seen_religions.add(r.id)
                founder = sim.agents.get(r.origin_id)
                founder_name = founder.state.name if founder else "Desconhecido"
                self._publish(tick,
                    f"Nova Religião: {r.name} fundada por {founder_name}",
                    f"{founder_name} estabeleceu {r.name}, baseada em "
                    f"{' e '.join(r.beliefs[:2])}. A fé já conquista seguidores.",
                    "culture", "major",
                    source_type="religion", source_id=r.id,
                    related_agent_ids=[r.origin_id],
                )

        if ideo_count > self._last_ideology_count:
            new_ideos = [
                i for i in sim.ideology_system.ideologies.values()
                if i.id not in getattr(self, '_seen_ideologies', set())
            ]
            if not hasattr(self, '_seen_ideologies'):
                self._seen_ideologies = set()
            for i in new_ideos:
                self._seen_ideologies.add(i.id)
                founder = sim.agents.get(i.origin_id)
                founder_name = founder.state.name if founder else "Desconhecido"
                self._publish(tick,
                    f"Ideologia Emergente: {i.name}",
                    f"{founder_name} propôs {i.name}, defendendo "
                    f"{' e '.join(i.principles[:2]).lower()}.",
                    "culture", "major",
                    source_type="ideology", source_id=i.id,
                    related_agent_ids=[i.origin_id],
                )

        self._last_religion_count = rel_count
        self._last_ideology_count = ideo_count

    def _check_demographics(self, current, prev, sim, tick):
        if prev:
            pop_delta = current.alive - prev.alive
            if pop_delta < -5:
                self._publish(tick,
                    f"População em declínio: {abs(pop_delta)} agentes perdidos",
                    f"O número de agentes vivos caiu de {prev.alive} para {current.alive}. "
                    f"Causas podem incluir mortes por idade ou crise.",
                    "society", "major",
                )

        if current.alive >= 100 and (self._last_pop < 100 or tick == 0):
            self._publish(tick,
                f"Marco Populacional: {current.alive} agentes",
                f"A população de Pangeia atingiu {current.alive} agentes conscientes, "
                f"um marco no desenvolvimento da civilização.",
                "society", "breaking",
            )
        self._last_pop = current.alive

    def _check_random_events(self, sim, tick):
        for event in sim.event_system.event_history:
            if not hasattr(self, '_last_event_idx'):
                self._last_event_idx = -1
                event_list = sim.event_system.event_history
                if event_list:
                    self._last_event_idx = len(event_list) - 1
                return

        event_list = sim.event_system.event_history
        if not event_list:
            return

        start = max(0, getattr(self, '_last_event_idx', -1) + 1)
        for i in range(start, len(event_list)):
            ev = event_list[i]
            severity = "major" if ev["severity"] > 0.5 else "minor"
            if ev["severity"] > 0.7:
                severity = "breaking"
            self._publish(tick,
                ev["name"],
                ev["description"][:200],
                self._event_category(ev["type"]),
                severity,
                source_type="world_event", source_id=ev["type"],
            )

        self._last_event_idx = len(event_list) - 1

    def _event_category(self, event_type: str) -> str:
        mapping = {
            "economic_crisis": "economy",
            "scientific_breakthrough": "science",
            "natural_disaster": "society",
            "epidemic": "society",
            "energy_crisis": "economy",
            "technological_advance": "technology",
            "cultural_renaissance": "culture",
        }
        return mapping.get(event_type, "society")

    def _check_milestones(self, current, sim, tick):
        pop = current.alive
        if pop >= 500 and self._last_pop < 500:
            self._publish(tick,
                f"500 Agentes: População atinge meio milhar",
                f"Pangeia ultrapassa 500 agentes conscientes — a complexidade social "
                f"cresce exponencialmente com o tamanho da população.",
                "society", "breaking",
            )

        if sim.technology:
            tech_count = sum(1 for t in sim.technology.technologies.values() if t.discovered)
            if tech_count >= 10:
                self._publish(tick,
                    f"Dez tecnologias dominadas — era de inovação",
                    f"Pangeia já domina {tech_count} tecnologias em diversas áreas do conhecimento.",
                    "technology", "major",
                )

    def _digest(self, current, sim, tick):
        metrics = sim.metrics
        recent = metrics.history[-10:] if len(metrics.history) >= 10 else metrics.history
        if not recent:
            return

        avg_happiness = sum(m.collective_happiness for m in recent) / len(recent)
        avg_stability = sum(m.stability for m in recent) / len(recent)

        econ = sim.economy
        digest_headline = f"📰 Pangeia Digest — Tick {tick}"
        digest_body = (
            f"População: {current.alive} agentes | "
            f"Felicidade: {avg_happiness:.0%} | "
            f"Estabilidade: {avg_stability:.0%} | "
            f"PIB: {econ.indicators.gdp:.1f} | "
            f"Desigualdade: {econ.indicators.inequality:.0%} | "
            f"Tecnologias: {sum(1 for t in sim.technology.technologies.values() if t.discovered) if sim.technology else 0}"
        )
        self._publish(tick,
            digest_headline, digest_body, "digest", "minor",
        )

    def query(self, category: Optional[str] = None,
              severity: Optional[str] = None,
              limit: int = 20, offset: int = 0) -> List[NewsArticle]:
        result = self.articles
        if category:
            result = [a for a in result if a.category == category]
        if severity:
            result = [a for a in result if a.severity == severity]
        result = result[-limit - offset:] if limit else result
        return result[offset:offset + limit]

    def get(self, article_id: str) -> Optional[NewsArticle]:
        for a in self.articles:
            if a.id == article_id:
                return a
        return None

    def latest(self, n: int = 10) -> List[NewsArticle]:
        return self.articles[-n:]

    def summary(self) -> dict:
        counts = {}
        for a in self.articles:
            counts[a.category] = counts.get(a.category, 0) + 1
        return {
            "total_articles": len(self.articles),
            "by_category": counts,
            "breaking": sum(1 for a in self.articles if a.severity == "breaking"),
        }
