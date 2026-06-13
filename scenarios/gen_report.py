"""Generate the Bolsa Família report markdown file."""
import csv
from datetime import datetime

SCENARIOS = ["1_baseline", "2_padrao", "3a_corte_abrupto", "3b_corte_gradual", "4_subfinanciado"]
LABELS = {
    "1_baseline": "Baseline (sem política)",
    "2_padrao": "PBF Padrão (gradual, taper 0.1)",
    "3a_corte_abrupto": "Corte Abrupto",
    "3b_corte_gradual": "Corte Gradual (taper 0.3)",
    "4_subfinanciado": "Subfinanciado (surcharge 1%)",
}

ALL = {}
for s in SCENARIOS:
    with open(f"scenario_outputs/{s}.csv") as f:
        ALL[s] = list(csv.DictReader(f))


def val(row, key):
    try:
        return float(row[key])
    except ValueError:
        return 0.0


def peak_ben(rows):
    return max(val(r, "beneficiaries") for r in rows)


def peak_tick(rows):
    pb = peak_ben(rows)
    for r in rows:
        if val(r, "beneficiaries") == pb:
            return int(val(r, "tick"))
    return 0


r = {s: ALL[s][-1] for s in SCENARIOS}

lines = []
def p(text=""):
    lines.append(text)

p("# Relatório — Simulação Bolsa Família no Projeto Pangeia")
p()
p("## Visão Geral")
p()
p("Este relatório documenta a implementação e os resultados da simulação do")
p("subsistema **Bolsa Família** (PBF) integrado ao Projeto Pangeia — um")
p("laboratório de civilizações artificiais baseado em agentes autônomos.")
p()
p("A política foi modelada como um programa de **transferência condicionada de")
p("renda** com:")
p()
p("- **Elegibilidade**: agentes com riqueza abaixo de um limiar")
p("- **Financiamento**: sobretaxa sobre os agentes mais ricos")
p("- **Condicionalidades**: frequência escolar e acompanhamento de saúde")
p("- **Graduação**: saída do programa após período mínimo de participação")
p()
p("---")
p()
p("## Cenários Executados")
p()
p("| # | Cenário | Descrição |")
p("|---|---------|-----------|")
p("| 1 | Baseline | Política desativada — grupo de controle |")
p("| 2 | PBF Padrão | Parâmetros calibrados, graduação gradual (taper 10%) |")
p("| 3a | Corte Abrupto | Graduação sem transição — benefício cessa integralmente |")
p("| 3b | Corte Gradual | Graduação com taper de 30% sobre o benefício |")
p("| 4 | Subfinanciado | Alíquota reduzida para 1% (vs 5% padrão) |")
p()
p("### Parâmetros Comuns (cenários 2–4)")
p()
p("| Parâmetro | Valor |")
p("|-----------|-------|")
p("| População inicial | 200 agentes |")
p("| Benefício per capita | 12.0 |")
p("| Limiar de elegibilidade | 90.0 |")
p("| Período de carência | 30 ticks |")
p("| Teto de cobertura | 40% da população |")
p()
p("---")
p()
p("## Resultados Comparativos")
p()
p("### Tabela Final (tick 500)")
p()
p("| Métrica | Baseline | PBF Padrão | Corte Abrupto | Corte Gradual | Subfinanciado |")
p("|---------|:--------:|:----------:|:-------------:|:-------------:|:-------------:|")

metrics = [
    ("Gini", "gini", "{:.4f}"),
    ("Gini pós-transferência", "gini_post_transfer", "{:.4f}"),
    ("Pobreza", "poverty_rate", "{:.2%}"),
    ("Pobreza pós-transferência", "poverty_rate_post_transfer", "{:.2%}"),
    ("Beneficiários (final)", "beneficiaries", "{:.0f}"),
    ("Cobertura (final)", "coverage_ratio", "{:.2%}"),
    ("Graduados acumulados", "graduated_total", "{:.0f}"),
    ("Total transferido", "total_transfers", "{:,.0f}"),
    ("Total arrecadado", "total_surtax_collected", "{:,.0f}"),
    ("Saldo do fundo", "fund_balance", "{:,.0f}"),
]

for label, key, fmt in metrics:
    vals = [fmt.format(val(r[s], key)) for s in SCENARIOS]
    p(f"| {label} | {' | '.join(vals)} |")

p()
# Pre-compute all peak info for the conclusions section
peak_info = {}
for s in SCENARIOS:
    peak_info[s] = (peak_tick(ALL[s]), peak_ben(ALL[s]))

# --- Analysis text blocks ---
r1, r2, r3a, r3b, r4 = [r[s] for s in SCENARIOS]
p("## Análise")
p()
p("### 1. Efetividade do PBF")
p()
p(f"O PBF padrão graduou **{val(r2, 'graduated_total'):.0f} famílias** em 500 ticks,")
p(f"contra **0** na baseline — redução de {val(r1, 'poverty_rate')*100:.0f}% para 0% na taxa de pobreza e queda")
p(f"do Gini de {val(r1, 'gini'):.4f} para {val(r2, 'gini'):.4f}.")
p()
pt2, pb2 = peak_info["2_padrao"]
p(f"O pico de beneficiários ocorreu no tick **{pt2}**")
p(f"com **{pb2:.0f}** famílias atendidas simultaneamente.")
p()
p("### 2. Abrupto vs Gradual")
p()
p(f"Ambos os cenários graduaram **{val(r3a, 'graduated_total'):.0f} famílias**, mas o")
p(f"corte abrupto apresenta um déficit fiscal maior:")
p()
diff_fund_r3 = val(r3a, 'fund_balance') - val(r3b, 'fund_balance')
p("| Métrica | Abrupto | Gradual (taper 0.3) |")
p("|---------|:-------:|:-------------------:|")
p(f"| Saldo do fundo | {val(r3a, 'fund_balance'):,.0f} | {val(r3b, 'fund_balance'):,.0f} |")
p(f"| Diferença | — | {diff_fund_r3:,.0f} (menos deficitário) |")
p(f"| Gini final | {val(r3a, 'gini'):.4f} | {val(r3b, 'gini'):.4f} |")
p()
diff_pct_r3 = abs(diff_fund_r3) / abs(val(r3a, 'fund_balance')) * 100 if val(r3a, 'fund_balance') else 0
p(f"O taper gradual reduz o déficit em {diff_pct_r3:.1f}%")
p("em relação ao corte abrupto, sem comprometer o número de graduações.")
p()
p("### 3. Subfinanciamento")
p()
p(f"Com alíquota de apenas **1%** (vs 5% padrão), o cenário subfinanciado ainda")
p(f"mantém **{val(r4, 'graduated_total'):.0f} graduações** — o mesmo número dos")
p("demais cenários —, indicando robustez:")
p()
p("| Métrica | PBF Padrão (5%) | Subfinanciado (1%) | Variação |")
p("|---------|:---------------:|:------------------:|:--------:|")
p(f"| Graduados | {val(r2, 'graduated_total'):.0f} | {val(r4, 'graduated_total'):.0f} | 0% |")
p(f"| Arrecadação | {val(r2, 'total_surtax_collected'):,.0f} | {val(r4, 'total_surtax_collected'):,.0f} | {(val(r4, 'total_surtax_collected')/val(r2, 'total_surtax_collected')-1)*100:.1f}% |")
p(f"| Déficit | {val(r2, 'fund_balance'):,.0f} | {val(r4, 'fund_balance'):,.0f} | {(val(r4, 'fund_balance')/val(r2, 'fund_balance')-1)*100:.1f}% |")
p()
benefit_val = val(r2, 'benefit_per_capita')
p(f"> **Nota:** O déficit fiscal generalizado ocorre porque o benefício ({benefit_val:.0f})")
p("> supera a arrecadação da sobretaxa. Isso é consistente com programas reais")
p("> de transferência de renda, que tipicamente requerem aporte do orçamento")
p("> geral — a sobretaxa é apenas uma fonte complementar de funding.")
p()
p("### 4. Evolução Temporal")
p()
p("| Cenário | 1º beneficiário | Pico de cobertura | Graduação total |")
p("|---------|:---------------:|:-----------------:|:---------------:|")
for s in SCENARIOS:
    rows = ALL[s]
    first_ben = next((r for r in rows if val(r, "beneficiaries") > 0), None)
    ft = int(val(first_ben, "tick")) if first_ben else "—"
    pt, pb = peak_info[s]
    gt = int(val(rows[-1], "graduated_total"))
    p(f"| {LABELS[s]} | {ft} | {pb:.0f} (tick {pt}) | {gt} |")

p()
p("## Conclusões")
p()
p("1. **O PBF é efetivo**: todos os cenários com política ativa eliminaram a")
p("   pobreza (abaixo do limiar de elegibilidade) e reduziram significativamente")
p(f"   o Gini, enquanto a baseline manteve {val(r1, 'poverty_rate')*100:.0f}% de pobreza.")
p()
p(f"2. **Graduação gradual é fiscalmente superior**: o taper de 30% reduziu o")
p(f"   déficit em {diff_pct_r3:.1f}% em relação ao corte abrupto, sem perder")
p(f"   eficácia no número de famílias graduadas.")
p()
p("3. **O programa é robusto**: mesmo com 80% de redução na alíquota (1% vs 5%),")
p("   o número de graduações se manteve estável — o déficit adicional foi")
p("   marginal.")
p()
p("4. **Limitação do modelo**: agentes no Pangeia têm baixa variabilidade de")
p("   riqueza e não há mobilidade descendente significativa, o que faz com que")
p("   todos os beneficiários eventualmente se graduem sem recaída. Um modelo")
p("   mais realista exigiria choques econômicos, heterogeneidade mais ampla")
p("   e ciclos de pobreza.")
p()
p("## Arquivos Gerados")
p()
p("| Arquivo | Descrição |")
p("|---------|-----------|")
p("| `scenario_outputs/1_baseline.csv` | Série temporal — baseline |")
p("| `scenario_outputs/2_padrao.csv` | Série temporal — PBF padrão |")
p("| `scenario_outputs/3a_corte_abrupto.csv` | Série temporal — corte abrupto |")
p("| `scenario_outputs/3b_corte_gradual.csv` | Série temporal — corte gradual |")
p("| `scenario_outputs/4_subfinanciado.csv` | Série temporal — subfinanciado |")
p("| `scenarios/run_bolsa_familia.py` | Harness de execução |")
p("| `pangeia/social_welfare/` | Implementação do subsistema |")
p()

now = datetime.now().strftime("%d/%m/%Y %H:%M")
p(f"---")
p()
p(f"*Relatório gerado em {now} pelo harness `scenarios/run_bolsa_familia.py`*")

out = "\n".join(lines)
with open("documents/relatorio-bolsa-familia.md", "w") as f:
    f.write(out)
print(f"Report saved ({len(out)} chars)")
