"""Classe Orientacao: um registro da base de conhecimento (um dicionário do JSON)."""

CAMPOS_OBRIGATORIOS = (
    "id", "categoria", "titulo", "palavras_chave", "resposta",
    "documentos", "onde", "fonte", "verificado_em",
)

AVISO_OFICIAL = "Aviso: este assistente NÃO é um canal oficial. Confirme na fonte indicada."


class Orientacao:
    """Guarda os dados de uma orientação e sabe se exibir na tela."""

    def __init__(self, id, categoria, titulo, palavras_chave, resposta,
                 documentos, onde, fonte, verificado_em, limitacao=""):
        self.id = id
        self.categoria = categoria
        self.titulo = titulo
        self.palavras_chave = palavras_chave
        self.resposta = resposta
        self.documentos = documentos
        self.onde = onde
        self.fonte = fonte
        self.verificado_em = verificado_em
        self.limitacao = limitacao  # campo extra da equipe: o que o assistente não garante

    @classmethod
    def de_dicionario(cls, dados):
        """Cria uma Orientacao a partir de um dicionário do JSON.

        Lança ValueError se faltar algum campo obrigatório ou se as listas vierem erradas.
        """
        faltando = [campo for campo in CAMPOS_OBRIGATORIOS if campo not in dados]
        if faltando:
            raise ValueError("campos faltando: " + ", ".join(faltando))
        if not isinstance(dados["palavras_chave"], list) or not isinstance(dados["documentos"], list):
            raise ValueError("palavras_chave e documentos precisam ser listas")
        return cls(
            dados["id"], dados["categoria"], dados["titulo"], dados["palavras_chave"],
            dados["resposta"], dados["documentos"], dados["onde"], dados["fonte"],
            dados["verificado_em"], dados.get("limitacao", ""),
        )

    def exibir(self):
        """Mostra a orientação completa, sempre com fonte, data e aviso."""
        print()
        print(f">> {self.titulo} [{self.categoria}]")
        print(self.resposta)
        print("Documentos necessários:")
        for documento in self.documentos:
            print(f"  - {documento}")
        print(f"Onde: {self.onde}")
        if self.limitacao:
            print(f"Limitação: {self.limitacao}")
        print(f"Fonte: {self.fonte} (verificado em {self.verificado_em})")
        print(AVISO_OFICIAL)
        print()
