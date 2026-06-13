# Bolsa Família, a Curva que Não Era e o Pé de Meia que Rende

## 1. Um laboratório que não mente por convicção

O Pangeia é um laboratório de civilizações artificiais. Agentes nascem, trabalham, acumulam, perdem. Não têm ideologia. Não votam, não torcem, não têm Twitter. Por isso, quando algo dá errado dentro dele, o erro não é político. É **aritmético**.

Decidimos modelar o Bolsa Família como subsistema desse laboratório. Transferência condicionada de renda, financiada por uma sobretaxa sobre os agentes mais ricos. A pergunta que guiou o experimento era simples, quase ingênua: **uma sobretaxa sobre riqueza consegue se autofinanciar no longo prazo?**

A resposta inicial foi não. Mas o motivo dessa resposta levou a outra pergunta, maior, que só apareceu depois: quando uma simulação falha, o que falhou de fato? A política que ela tentou descrever, ou a teoria de riqueza que foi embutida nela, em silêncio, antes de qualquer linha sobre o Bolsa Família ser escrita?

Este ensaio começa tentando responder a primeira pergunta. Termina respondendo a segunda.

## 2. O modelo sem capital

Na primeira rodada, sem nenhuma política ativa, a população de 200 agentes chegou a um Gini de 0,4748 e 38% de pobreza. Números familiares. Próximos do Brasil real.

Com o Bolsa Família ativado, 128 famílias foram graduadas, a pobreza foi a zero, o Gini caiu para algo perto de 0,06. Eficácia perfeita. Excessivamente perfeita, na verdade. Modelo nenhum, e nenhuma política, produz isso no mundo real. Quando um experimento devolve um resultado bonito demais, a primeira suspeita não deve ser sobre a política. Deve ser sobre o modelo.

### 2.1. Abrupto, gradual, e o que a convergência esconde

Testamos duas formas de tirar o benefício de quem se qualifica para sair: corte abrupto, tudo de uma vez, e corte gradual, em transição.

No fim, os dois cenários chegam ao mesmo lugar. Mesmas 128 graduações. Gini final quase idêntico. Se alguém olhasse só o resultado final, diria: **não importa como você sai, o destino é o mesmo**.

É mentira. No tick 30, o corte abrupto remove 80 famílias do programa de uma só vez. O corte gradual mantém essas mesmas 80 famílias em transição por mais dois ou três ticks, com benefício decrescente. O gradual gasta 1.843 unidades a mais no total. Essa diferença não aparece no resultado final. Aparece no **meio do caminho**.

É precisamente esse tipo de inversão que costuma justificar políticas mal desenhadas. *No fim dá tudo igual, então a forma não importa.* Mas a forma é o que se vive. Ninguém vive o resultado final de uma política. Vive-se a transição. Vive-se o tick 30.

### 2.2. O pé de meia que se esvai

Por que, então, a política inteira converge para o mesmo lugar, independente de como é desenhada? A resposta estava na sobretaxa.

A sobretaxa do Pangeia incide sobre **estoque**. Sobre patrimônio acumulado, `wealth`, não sobre fluxo, não sobre renda. A cada tick, `wealth -= surcharge`. A própria cobrança reduz a base sobre a qual ela incide.

A 5% de alíquota, a elite caiu abaixo do limiar de tributação em cerca de 30 ticks. A 1%, levou perto de 100. No fim, a arrecadação total convergiu para aproximadamente o mesmo valor nos dois casos, em torno de 40 mil unidades. **Uma curva de Laffer sem desincentivo ao trabalho.** Ninguém deixou de produzir porque a alíquota subiu. A base simplesmente foi consumida antes de poder ser tributada de novo.

É como tributar o pé de meia em vez dos juros que ele gera. Taxe o principal repetidamente, sem que ele se reponha, e qualquer alíquota positiva eventualmente o esvazia. A diferença entre 1% e 5% não é se a base vai erodir. É **quanto tempo até erodir**.

Vale nomear o que aconteceu com precisão. A curva de Laffer, na forma como costuma ser ensinada, é um fenômeno comportamental: acima de certa alíquota, as pessoas reagem, sonegam, investem menos, trabalham menos, e a arrecadação cai. Nada disso está presente aqui. Nenhum agente decidiu produzir menos. A arrecadação caiu porque a base foi consumida, tick a tick, antes de poder ser tributada de novo. **Nem toda erosão da base tributária é comportamental. Algumas são puramente dinâmicas.**

### 2.3. A hipótese oculta do bolo fixo

O Pangeia, sem que ninguém tivesse essa intenção, modelou uma premissa que raramente é declarada, e por isso raramente é discutida. Ninguém, no debate público, afirma literalmente que riqueza não cresce. Até os defensores mais convictos de baixa tributação sobre patrimônio reconhecem que capital rende, é parte do argumento deles: tributar espantaria esse rendimento. A premissa não está nas palavras de ninguém. Está no **enquadramento**: na forma como o problema é posto, riqueza aparece como algo que se tem, não como algo que se reproduz. O bolo existe, sim, ninguém nega isso. A pergunta que quase nunca aparece é se ele cresce enquanto está sendo dividido.

No Pangeia essa pergunta nunca apareceu porque a resposta já estava decidida, por omissão, antes do experimento começar. Não havia `wealth *= 1 + r`. Não havia retorno sobre capital. E o modelo, sem dizer nada, sem que ninguém o tivesse instruído a tomar partido, operou exatamente como se a resposta fosse não. Essa é a utilidade do experimento: ele não revela o que alguém pensa. Revela o que um sistema **faz**, quando uma pergunta nunca é feita.

## 3. O que muda quando o pé de meia rende

Adicionamos retorno de capital. Elite, acima de 500 de patrimônio, passou a receber 1% por tick, algo como 12,7% ao ano, comparável ao que FIIs e renda fixa pagam no Brasil hoje. Faixa intermediária, entre 200 e 500, recebeu 0,3%, perto de 3,7% ao ano. O resto, nada. A referência, explícita, é Piketty: `r > g`, o retorno do capital tende a superar o crescimento da economia, e essa diferença é o motor da concentração.

A simulação não descobriu uma lei nova. A regra que cada agente segue, ganhar `r` e perder `τ` por tick, era exatamente a regra escrita no código. Não há mistério aí, e seria desonesto fingir que há. A trajetória de um agente, tick a tick, é simplesmente:

```
W(t+1) = W(t) · (1 + r − τ)
```

O que essa equação faz não é revelar algo escondido. É **nomear**, com precisão, algo que já tínhamos visto sem entender por quê: por que a arrecadação converge para ~40k independente da alíquota quando `r=0`, e por que isso deixa de acontecer quando `r>0`. A regra local é trivial. O que era genuinamente emergente, e que a equação só agora deixa visível, é a interação dessa regra com o limiar de elegibilidade do PBF, com a entrada e saída de agentes da faixa tributável, com a própria base se recompondo ou não ao longo de 500 ticks. Ninguém programou essa convergência. Ela surgiu do encontro entre uma regra simples e um sistema com realimentação. A equação é o resumo depois do fato, não a profecia antes dele.

Os três regimes que ela descreve, se `r > τ` o estoque cresce, se `r = τ` permanece estável, se `r < τ` encolhe, apareceram nos dados. Mas apareceram porque foram colocados ali. A pergunta que vale a pena é outra: dado que essa regra simples estava no código desde o início do cenário 5, por que sua consequência só ficou visível quando comparamos com o cenário onde ela não existia? A resposta é que premissas não se revelam por inspeção do código. Revelam-se por contraste com o mundo em que não estavam.

Os resultados:

```
                          Coletado   Fundo     Elite remanescente
  Padrão  (5%, s/ retorno)  43.158    -9.834       0
  Subfin. (1%, s/ retorno)  42.148   -10.844       0
  5a      (5%, c/ retorno)  44.997    -7.995       0
  5b      (1%, c/ retorno)  60.053    +7.061       1
```

Apenas um cenário termina com superávit fiscal: 5b, alíquota de 1% com retorno de capital. E apenas nesse cenário sobrevive, ao final, algum agente classificado como elite.

A coincidência não é coincidência. O Estado simulado só se sustenta financeiramente no único cenário em que ainda existe alguém rico o bastante para sustentá-lo. **O superávit e a desigualdade persistente são a mesma coisa, vista de dois lados.**

Vale insistir nisso, porque é fácil ler a tabela na direção errada. Um superávit fiscal sustentado por um único agente concentrando riqueza não é estabilidade. É dependência. Um Estado cuja arrecadação depende da sobrevivência de um punhado de fortunas não está numa posição confortável, está numa posição de captura: qualquer evento que reduza essa fortuna, um imposto mal calibrado, uma crise, uma sucessão, leva o fundo de volta ao déficit. O número "+7.061" no cenário 5b não é uma vitória da política fiscal. É a fotografia de um sistema que aposta tudo em poucas peças.

A condição que separa os regimes já está escrita acima, na própria equação: `τ ≤ r`. Abaixo dessa linha, `(1 + r − τ) > 1`, e a base se repõe mais rápido do que é consumida. Acima dela, a sangria vence, e o destino é o mesmo de antes, mais lento, mas o mesmo.

Mas vale notar: mesmo em 5a, onde a alíquota de 5% continua acima do retorno de 1%, e a sangria ainda deveria vencer, o resultado melhorou em relação ao cenário padrão sem retorno. Mais coletado, menos déficit. A fronteira entre o patrimônio que se sustenta e o que se esvai não é um precipício. É uma inclinação. Há graus entre sustentar e erodir, e o tempo que se ganha numa inclinação suave às vezes é tempo suficiente para tudo o que importa.

## 4. O que isso diz sobre o debate real

### 4.1. Aritmética, não comportamento

O debate público brasileiro sobre tributar grandes fortunas costuma se polarizar entre dois discursos. Um lado defende alíquotas mais altas de IR para os mais ricos. O outro responde que tributar desincentiva o investimento, espanta capital, reduz a produção.

O Pangeia sugere um terceiro efeito, que não depende de comportamento algum. **Taxar patrimônio corrói a própria base, independente de qualquer reação do contribuinte.** O agente do modelo não decide investir menos por revolta. Ele simplesmente possui menos, a cada tick, do que possuía antes. A erosão é mecânica. Aconteceria mesmo que o agente fosse perfeitamente racional, perfeitamente cooperativo, perfeitamente disposto a contribuir.

Isso não significa que tributar patrimônio seja um erro. Significa que a pergunta certa não é *isso desincentiva os ricos?*, mas **sobre o que, exatamente, a alíquota incide, e a que velocidade essa coisa se repõe**. É a pergunta que a seção seguinte tenta responder.

### 4.2. Estoque, fluxo, e a composição que ninguém discute

No Brasil real, o retorno médio de um FII de qualidade gira perto de 12% ao ano, confortavelmente acima de qualquer alíquota razoável sobre patrimônio. Sob essa luz, `τ < r` não é uma curiosidade de modelo. É uma descrição plausível da realidade: um imposto sobre grandes patrimônios poderia ser sustentável, **se incidisse sobre o patrimônio certo**.

O debate político discute alíquotas marginais de Imposto de Renda sem nunca discutir a **composição patrimonial** de quem seria afetado. Renda do trabalho é fluxo puro, consumido em sua maior parte, sem estoque que se reponha. Patrimônio financeiro é estoque que gera fluxo, e pode sustentar uma alíquota indefinidamente, desde que ela não supere o próprio rendimento. Tratar essas duas coisas como a mesma categoria fiscal é, possivelmente, o erro de modelagem mais antigo do debate tributário brasileiro. Mais antigo, e mais real, do que qualquer linha de código.

### 4.3. O retorno é uma abstração, e a abstração tem nome

É preciso dizer com clareza: aquele 1% por tick não é nada concreto. É juro, é dividendo, é aluguel, tudo junto, achatado numa única taxa fixa. Na vida real, nem todo patrimônio rende igual. Um imóvel onde se mora não rende nada, em termos de caixa. Uma ação rende, mas de forma volátil, sujeita a ciclos, crises, humor de mercado.

Há algo mais embutido nessa abstração, e merece ser dito sem rodeios: no Pangeia, o capital rende porque o código decidiu que rende. O retorno é exógeno. Não vem de produtividade, de inovação, de competição, de risco assumido. É um número fixo, escrito de fora.

Isso não invalida o achado, mas muda o que ele significa. Enquanto o retorno for exógeno, o modelo continua sendo, no fundo, **redistributivo**: ele move riqueza que já existe, segundo regras que já existem. A pergunta natural, e que este ensaio não responde, é de onde vem o retorno. Se o rendimento passar a emergir de produção econômica efetiva, algo que os agentes fazem, não algo que lhes é dado, o modelo deixa de ser apenas redistributivo e passa a ser um **modelo de acumulação**. Essa distinção não é de grau. É de espécie.

Há uma assimetria que precisa ser dita, porque o ensaio inteiro se apoia em desfazer uma assimetria parecida do lado da curva de Laffer tradicional. Lá, criticamos a ideia de que tributar sempre muda comportamento. Aqui, do lado do retorno, fazemos exatamente a suposição oposta sem questionar: que tributar **nunca** muda o retorno. Que `r` permanece 12,7% independente de `τ`. Na vida real, uma alíquota mais alta pode reduzir preços de ativos, afastar investidores, alterar o próprio `r` que sustenta a equação. O modelo trata `r` e `τ` como se fossem independentes. Não há razão forte para crer que sejam. Essa é, talvez, a premissa mais conveniente de todo o experimento, e a que recebeu menos escrutínio.

## 5. Os limites do que foi simulado, e por que eles importam mais que os resultados

O modelo tributa estoque, não fluxo. Não há Imposto de Renda, não há IOF, não há nenhuma das centenas de incidências que compõem um sistema tributário real. O retorno de capital é fixo, não responde à alíquota, não reage a incentivos, como já discutido. E, mais importante: **a riqueza, no Pangeia, nunca sofre um choque exógeno**. Só sobe, por trabalho ou retorno, ou desce, por sobretaxa. Nunca quebra, nunca é assaltada, nunca perde metade do valor numa crise. Seria interessante, em outro momento, testar um retorno volátil, com ciclos e correções, e ver se `τ ≤ r` deixa de ser uma linha fixa e passa a ser uma probabilidade que varia no tempo.

Há ainda uma limitação mais sutil, escondida na própria métrica que usamos para julgar o cenário 5b como sucesso. Chamamos de "elite remanescente" o fato de que, ao final, ainda existia ao menos um agente acima do limiar de tributação. Tratamos isso como sinal de sustentabilidade fiscal. Mas a existência de ricos e a existência de uma **base produtiva ampla** não são a mesma coisa. Um bilionário sustentando toda a arrecadação e mil agentes de patrimônio médio sustentando a mesma arrecadação podem produzir o número idêntico no fundo do programa, e significar coisas opostas sobre a estrutura da sociedade simulada. O modelo atual não distingue riqueza concentrada de riqueza distribuída, quando ambas geram o mesmo fluxo de caixa para o Estado. Medir a concentração *dentro* do grupo que sustenta a arrecadação, não apenas constatar que esse grupo existe, é o próximo passo óbvio.

É tentador tratar essas limitações como nota de rodapé. Não são. Elas são, possivelmente, o achado mais importante de todo o experimento, e o mais incômodo.

Porque toda simulação que pretende informar política pública embute, nessas ausências, uma teoria sobre como o mundo funciona. Um modelo sem choques é um modelo que assume estabilidade. Uma planilha do Ministério da Fazenda que projeta arrecadação a dez anos sem prever recessão está fazendo exatamente a mesma aposta silenciosa que o Pangeia fez, sem querer, na primeira rodada. A diferença é que o Pangeia confessa, no código, o que assumiu. A planilha, geralmente, não.

## 6. Conclusão

O Pangeia, sem intenção, modelou a armadilha do bolo fixo. E então, ao acrescentar uma única linha, retorno sobre capital, inverteu o resultado. `τ < r` produziu superávit onde antes só havia déficit crescente. A diferença entre as duas histórias não está em nenhuma decisão sobre o Bolsa Família. Está numa decisão anterior, quase invisível, sobre **o que conta como riqueza e como ela se move**.

Toda política fiscal real enfrenta essa escolha, ainda que não a nomeie. Taxar estoque ou taxar fluxo. Taxar o pé de meia ou taxar os juros que ele rende. A escolha determina se a base que sustenta a política se repõe ou se esvai, e nenhuma quantidade de debate sobre alíquotas resolve isso, se a pergunta sobre **o que está sendo taxado** continuar sem resposta.

O laboratório não tinha opinião sobre o Bolsa Família. Mas, ao tentar simular um, foi obrigado a tomar uma posição sobre o que é riqueza. E essa posição, mais do que qualquer número de Gini, é o que realmente importa.

Nada disso prediz o que vai acontecer com a economia brasileira. O modelo não tem imóveis, não tem dívida, não tem herança, não tem choques, não tem liquidez. Qualquer número absoluto que ele produz, 60.053 coletados, +7.061 de superávit, é verdadeiro apenas dentro de um mundo que não existe. O valor do experimento não está nesses números. Está no fato de que, para produzi-los, o modelo precisou tomar uma decisão sobre o que conta como riqueza, e essa decisão, uma vez tomada, determinou tudo o que veio depois.

Por ora, o Pangeia trata riqueza como massa: um número que um agente possui, sobe ou desce, e ponto. É uma física newtoniana da riqueza. Essa física não foi descoberta aqui, ela é antiga, é a física de qualquer planilha. O que o experimento fez foi torná-la **visível**, ao colocá-la ao lado de um mundo onde ela não valia, e observar a diferença. Riqueza real também é rede, é relação, é a posição que algo ocupa em relação a outras coisas, não apenas a quantidade que possui. A física que vem depois de Newton ainda não foi escrita aqui. Mas, ao menos agora, sabemos que ainda não foi.

E sabemos onde procurar. A ausência de `wealth *= 1+r` não estava escondida em nenhum discurso, em nenhuma justificativa, em nenhuma entrelinha que exigisse interpretação. Estava num lugar exato do código, uma linha que não existia, e só por isso pôde ser apontada, comparada, corrigida. Ler o superávit de 5b como dependência, não como vitória, foi possível pelo mesmo gesto: tratar o que parecia positivo como o lugar onde a estrutura, e sua fragilidade, ficavam expostas. A pergunta que sobra não é sobre o Pangeia. É sobre os outros modelos, os que projetam arrecadação, os que sustentam reformas da Previdência, os que chegam a comissões parlamentares com a etiqueta de evidência. Quantos deles têm, em algum lugar, uma linha que não foi escrita, e que ninguém, até hoje, teve motivo para notar que faltava?

---

## Apêndice: dados citados

### Valores finais (tick 500)

| Métrica | Baseline | PBF Padrão | Abrupto | Gradual 0.3 | Subfinanc. |
|---|---|---|---|---|---|
| Gini | 0,4748 | 0,0640 | 0,0639 | 0,0633 | 0,0511 |
| Pobreza | 38% | 0% | 0% | 0% | 0% |
| Graduados | 0 | 128 | 128 | 128 | 128 |
| Total transferido | 0 | 52.992 | 46.080 | 47.923 | 52.992 |
| Total arrecadado | 0 | 43.140 | 36.221 | 38.173 | 42.129 |
| Saldo do fundo | 0 | -9.852 | -9.859 | -9.751 | -10.863 |

### Evolução, abrupto vs. gradual (tick 30–100)

| tick | Abrupto (benef/grad/disp) | Gradual 0.3 (benef/grad/disp) |
|---|---|---|
| 0 | 80 / 0 / 960 | 80 / 0 / 960 |
| 30 | 48 / 80 / 29.376 | 80 / 0 / 29.472 |
| 32 | 48 / 80 / 30.528 | 0 / 80 / 29.952 |
| 100 | 0 / 128 / 46.080 | 0 / 128 / 47.923 |

### Cenário 5: capital returns

```
                          Coletado   Fundo     Elite remanescente (n>180)
  Padrão  (5%, s/ retorno)  43.158    -9.834       0
  Subfin. (1%, s/ retorno)  42.148   -10.844       0
  5a      (5%, c/ retorno)  44.997    -7.995       0
  5b      (1%, c/ retorno)  60.053    +7.061       1
```

Calibração do retorno: elite (patrimônio > 500) recebe 1% por tick (~12,7% a.a.); faixa intermediária (200–500) recebe 0,3% por tick (~3,7% a.a.); demais agentes, 0%.
