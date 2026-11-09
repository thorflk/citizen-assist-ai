"""Converte as fichas do Mapiii (data/kb.json) para a base do assistente em Python.

Uso: python gerar_base.py <kb.json do Mapiii> <base_conhecimento.json de saída>
Os textos vêm das fichas (conferidas nas fontes oficiais); só título, categoria e
palavras-chave são escritos aqui.
"""
import json
import sys

kb = json.load(open(sys.argv[1], encoding="utf-8"))
por_id = {e["id"]: e for e in kb}

plano = [
    ("bilhete-unico-especial-pcd", "Transporte", "Pedir o Bilhete Único Especial da Pessoa com Deficiência",
     ["bilhete unico especial", "bilhete especial", "bilhete unico", "onibus de graca", "gratuidade no onibus",
      "metro de graca", "cadeirante paga onibus", "renovar bilhete", "segunda via do bilhete"]),
    ("atende-mais", "Transporte", "Pedir o Atende+, transporte porta a porta gratuito da Prefeitura",
     ["atende", "atende+", "van adaptada", "porta a porta", "transporte adaptado", "ficha de avaliacao medica",
      "surdocegueira", "van da prefeitura"]),
    ("passe-livre-interestadual", "Transporte", "Pedir o Passe Livre Interestadual (viagem gratuita entre estados)",
     ["passe livre", "passe livre interestadual", "antt", "outro estado", "viagem interestadual",
      "onibus interestadual", "passagem gratuita", "viajar de graca"]),
    ("bpc-pcd", "Benefícios", "Pedir o BPC (Benefício de Prestação Continuada) para pessoa com deficiência",
     ["bpc", "loas", "beneficio de prestacao continuada", "beneficio assistencial", "salario minimo",
      "salario do governo", "meu inss", "inss", "baixa renda", "pericia"]),
    ("isencao-ipi-iof-carro", "Carro e direção", "Pedir isenção de IPI e IOF na compra do carro",
     ["isencao", "ipi", "iof", "comprar carro", "compra de carro", "desconto no carro", "sisen",
      "receita federal"]),
    ("cartao-defis-estacionamento", "Carro e direção", "Pedir o Cartão DeFis para estacionar em vaga especial",
     ["defis", "cartao defis", "vaga especial", "vaga de deficiente", "estacionar", "estacionamento",
      "cartao de estacionamento", "zona azul"]),
    ("cnh-renovacao-pcd", "Carro e direção", "Renovar a CNH (carteira de motorista) da pessoa com deficiência",
     ["cnh", "renovar cnh", "renovacao da cnh", "carteira de motorista", "habilitacao", "detran",
      "junta medica especial", "exame pratico", "carro adaptado"]),
    ("calcada-publica-manutencao", "Calçadas", "Pedir conserto de calçada pública (praças e avenidas)",
     ["calcada publica", "consertar calcada", "conserto de calcada", "arrumar calcada", "calcada quebrada",
      "buraco na calcada", "arrumar a calcada", "consertar a calcada", "praca", "avenida"]),
    ("calcada-particular-denuncia", "Calçadas", "Denunciar calçada particular danificada ou inexistente",
     ["calcada particular", "denunciar calcada", "calcada danificada", "calcada inexistente", "sem calcada",
      "degrau na calcada", "calcada que nao existe", "nao tem calcada", "vizinho", "dono do imovel"]),
    ("calcada-obstaculo-acessibilidade", "Calçadas", "Pedir fiscalização de obstáculo na calçada",
     ["obstaculo", "obstaculo na calcada", "vaso na calcada", "barra de ferro", "barras de ferro",
      "corrente na calcada", "vaso", "bloqueando a calcada"]),
    ("central-156", "Canais da Prefeitura", "Falar com a Central 156 da Prefeitura de São Paulo",
     ["156", "central 156", "sp156", "telefone da prefeitura", "falar com a prefeitura",
      "atendimento da prefeitura", "falo com a prefeitura", "servico da prefeitura", "aplicativo sp156",
      "descomplica"]),
    ("ouvidoria-geral-municipio", "Canais da Prefeitura", "Reclamar na Ouvidoria Geral do Município",
     ["ouvidoria", "reclamar", "reclamar da prefeitura", "reclamacao", "finalizado", "prazo vencido",
      "mal atendido", "nao resolveram", "nao fez o servico", "sem resolver"]),
    ("reclamacao-onibus-sptrans", "Transporte", "Reclamar de motorista, cobrador ou fiscal de ônibus (SPTrans)",
     ["reclamar do onibus", "reclamacao da sptrans", "denunciar motorista", "motorista de onibus", "motorista",
      "cobrador", "tratou mal", "desrespeito", "nao esperou"]),
    ("ouvidoria-sptrans", "Transporte", "Recorrer à Ouvidoria da SPTrans quando a reclamação não foi resolvida",
     ["ouvidoria da sptrans", "ouvidoria sptrans", "email da sptrans", "e mail da sptrans", "sptrans nao respondeu",
      "sptrans nao resolveu", "nao resolveram", "reclamei", "recorrer da sptrans", "segunda instancia"]),
]

saida = []
for numero, (kid, categoria, titulo, chaves) in enumerate(plano, start=1):
    ficha = por_id[kid]
    onde = ficha["onde"]["texto"]
    if ficha["onde"].get("link"):
        onde += " Link: " + ficha["onde"]["link"]
    saida.append({
        "id": numero,
        "categoria": categoria,
        "titulo": titulo,
        "palavras_chave": chaves,
        "resposta": ficha["resumo"] + " Prazo: " + ficha["prazo_tipico"],
        "documentos": ficha["documentos"],
        "onde": onde,
        "fonte": ficha["fonte_url"],
        "verificado_em": ficha["verificado_em"],
        "limitacao": ficha["limitacao"],
    })

with open(sys.argv[2], "w", encoding="utf-8", newline="\n") as arquivo:
    json.dump(saida, arquivo, ensure_ascii=False, indent=2)
    arquivo.write("\n")
print(len(saida), "orientacoes em", len({o['categoria'] for o in saida}), "categorias")
