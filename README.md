# Mapiii no terminal · Citizen Assist AI

Assistente em Python, executado no terminal, que orienta **pessoas com deficiência e suas famílias em São Paulo**, começando por quem usa cadeira de rodas, sobre direitos e serviços de transporte, benefícios e compra de carro. Toda resposta mostra a fonte oficial, a data em que a equipe conferiu a informação e o aviso de que **este assistente não é um canal oficial**.

Global Solution 2026.2 (CitizenTech), disciplina **Pensamento Computacional e Automação com Python**, turma 1CC, FIAP. É a versão em Python do nosso projeto da GS, o **Mapiii · o mapa dos seus direitos** ([repositório](https://github.com/GabrielRoma0/mapiii-assistente)).

## Integrantes

| Nome | RM |
|---|---|
| Thor Ferreira Camargo | 569543 |
| Gabriel Botelho Ronão | 570589 |

## Público e problema

**Público:** pessoas com deficiência (com foco em quem usa cadeira de rodas) e familiares que cuidam delas, na cidade de São Paulo.

**Problema:** os direitos existem (gratuidade no ônibus, transporte porta a porta, benefício de um salário mínimo, isenção na compra do carro), mas a informação fica espalhada entre SPTrans, INSS, ANTT e Receita Federal, em linguagem técnica e no meio de páginas que parecem oficiais e não são. A família perde tempo descobrindo o que pode pedir, que documentos levar e onde ir.

## ODS relacionados

- **ODS 10, Redução das desigualdades:** inclusão de pessoas com deficiência (meta 10.2).
- **ODS 11, Cidades e comunidades sustentáveis:** transporte acessível (meta 11.2).

## Como executar

Precisa do **Python 3.8 ou mais novo**. Não usa nenhuma biblioteca externa.

```bash
python main.py
```

Testes automáticos (20 testes, também sem bibliotecas externas):

```bash
python -m unittest discover tests
```

## Estrutura

```
citizen-assist-ai/
  README.md
  main.py                  cria a base e o assistente e inicia o menu
  orientacao.py            classe Orientacao (um registro do JSON)
  base_conhecimento.py     classe BaseConhecimento (carregar, categorias, busca)
  assistente.py            classe Assistente (atendimento, histórico, indicadores, CSV)
  data/
    base_conhecimento.json orientações conferidas pela equipe
    historico.json         atendimentos registrados (criado ao usar)
    avaliacoes.json        notas de facilidade de 1 a 5 (criado ao sair)
    atendimentos.csv       exportação do histórico (opção 4 do menu)
  tests/
    test_assistente.py     testes automáticos
```

### Classes e composição

```
Assistente
  nome, historico, avaliacoes
  base: BaseConhecimento
          caminho
          orientacoes: [Orientacao, Orientacao, ...]
```

| Classe | Atributos | Métodos |
|---|---|---|
| `Orientacao` | id, categoria, titulo, palavras_chave, resposta, documentos, onde, fonte, verificado_em, limitacao | `exibir()`, `de_dicionario()` |
| `BaseConhecimento` | caminho, orientacoes, erros | `carregar()`, `categorias()`, `por_categoria()`, `pontuar()`, `buscar()`, `buscar_id()` |
| `Assistente` | nome, base, historico, avaliacoes | `iniciar()`, `perguntar()`, `navegar()`, `registrar()`, `indicadores()`, `exportar_csv()`, `sobre()`, `encerrar()` |

O campo `limitacao` é um campo extra da equipe: diz o que o assistente não garante (por exemplo, quem decide o pedido).

## Regra de pontuação

A pergunta, as palavras-chave e o título são comparados com `normalizar()`: minúsculas, sem acentos e sem pontuação. Além dos sinais do enunciado, também tiramos aspas, `/` e `-`, para "porta-a-porta" virar "porta a porta". A comparação é por palavra inteira: "ipi" não casa com "municipio".

| Regra | Pontos |
|---|---|
| Palavra-chave da orientação que aparece na pergunta | +3 |
| Palavra da pergunta (4 letras ou mais) que aparece no título | +1 (cada palavra conta uma vez) |

| Melhor pontuação | Resultado |
|---|---|
| 6 ou mais | Confiança **ALTA** |
| 3 a 5 | Confiança **MÉDIA** |
| menos de 3 | "Não encontrei": sugere outras palavras e as categorias |

`buscar()` devolve uma lista de tuplas `(pontos, orientacao)` da maior para a menor. O assistente mostra a melhor e, se a pessoa disser que não ajudou, oferece até duas alternativas que também passaram de 3 pontos.

**Exemplo real:** "Autista tem isenção de IPI na compra do carro?" vira " autista tem isencao de ipi na compra do carro ". Para a orientação "Pedir isenção de IPI e IOF na compra do carro":

- palavras-chave na pergunta: "isencao" (+3) e "ipi" (+3) = 6. ("compra de carro" não casa, porque a pergunta diz "compra **do** carro.)
- palavras da pergunta com 4 letras ou mais que estão no título: "isencao", "compra" e "carro" (+1 cada) = 3.
- **total: 9 pontos, confiança ALTA.**

## Regras de atendimento

- **Navegação por categorias** com "0 para voltar" em todas as telas.
- **Entradas inválidas** (letras, número fora da faixa, resposta vazia, s/n inválido) repetem a pergunta e nunca encerram o programa.
- **Dados pessoais:** o assistente nunca pede nome, CPF, telefone ou e-mail. Pergunta com 8 ou mais dígitos ou com `@` é recusada e não é registrada nem conta como tentativa.
- **Transparência:** toda resposta mostra fonte, data de verificação e o aviso "este assistente NÃO é um canal oficial".
- **Arquivos:** se o JSON da base estiver ausente ou corrompido, o programa avisa e fecha sem erro. Se o `historico.json` estiver corrompido, ele é guardado como `historico.json.corrompido` e um novo começa, sem perder dados.

## Histórico e indicadores

Cada atendimento é salvo em `data/historico.json` com: data, origem (`pergunta` ou `categoria`), pergunta, id da orientação, se encontrou, se ajudou, tentativas e tempo em segundos (`time.time()` no começo e `round(time.time() - inicio, 1)` quando a orientação aparece).

- **Atendimento por pergunta:** começa na primeira pergunta. Cada pergunta não encontrada conta uma tentativa. Se a pessoa desiste (0), o atendimento entra como dúvida sem solução.
- **Atendimento por categoria:** conta 1 tentativa e o tempo até escolher a orientação.
- **Ao sair:** o assistente pede uma nota de facilidade de 1 a 5, guardada em `data/avaliacoes.json`.

Indicadores (opção 3 do menu): resposta encontrada (%), taxa de acerto (% de atendimentos em que a pessoa disse que ajudou), tempo médio para encontrar, tentativas por atendimento, facilidade de uso (média de 1 a 5) e lista de dúvidas sem solução. A opção 4 exporta tudo para `data/atendimentos.csv` com `csv.DictWriter`.

## Integração com outras disciplinas

- **Mapiii (projeto da GS):** a base de conhecimento vem das fichas que a dupla conferiu para o Mapiii, nas mesmas fontes oficiais e com as mesmas datas.
- **Computer Science:** _(a preencher)_ opção "Descobrir se posso ter direito", que usa a expressão booleana simplificada por mapa de Karnaugh no trabalho de Computer Science.

A busca por pontuação continua sendo o centro do assistente, como pede o enunciado.

## Fontes consultadas

| Orientação | Fonte | Conferida em |
|---|---|---|
| Bilhete Único Especial da Pessoa com Deficiência | https://bilheteunico.sptrans.com.br/especial/pessoa-com-deficiencia/ | 09/11/2026 |
| Atende+ | https://www.sptrans.com.br/media/1392/regulamento_atende-nov_17.pdf | 09/11/2026 |
| Passe Livre Interestadual | https://www.gov.br/pt-br/servicos/obter-passe-livre-interestadual-digital | 09/11/2026 |
| BPC para pessoa com deficiência | https://www.gov.br/inss/pt-br/direitos-e-deveres/beneficios-assistenciais/beneficio-assistencial-a-pessoa-com-deficiencia-bpc-loas | 09/11/2026 |
| Isenção de IPI e IOF na compra do carro | https://www.gov.br/receitafederal/pt-br/acesso-a-informacao/perguntas-frequentes/isencao-para-compra-de-carro | 09/11/2026 |

## Teste com usuários

_(a preencher depois do teste: pelo menos 3 pessoas de fora da equipe e 10 atendimentos. Sem nomes nem dados das pessoas.)_

| Indicador | Resultado |
|---|---|
| Pessoas que testaram | |
| Atendimentos | |
| Resposta encontrada | |
| Taxa de acerto (ajudou) | |
| Tempo médio para encontrar | |
| Tentativas por atendimento | |
| Facilidade de uso (1 a 5) | |

**Dúvidas sem solução:**

**Melhoria feita a partir do teste:**

## Limitações

- Só responde com o que está na base. Não entende frases que não usem nenhuma palavra-chave ou palavra do título.
- Não vê pedidos, não decide se a pessoa tem direito e não substitui SPTrans, INSS, ANTT ou Receita Federal.
- As informações valem na data de verificação e podem mudar. A base cobre só a cidade de São Paulo e direitos federais.
- A regra de dados pessoais conta todos os dígitos da pergunta: "lei 8.899/1994" tem 8 dígitos e também é recusada.
- A nota de facilidade é por sessão, não por atendimento.

## Vídeo técnico

_(a preencher: link do YouTube, não listado)_
