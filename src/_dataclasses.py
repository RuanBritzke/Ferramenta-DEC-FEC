from typing import Literal
from src._database import (
    pd,
    simo_to_code,
    encontrar_nucleo,
    multiplicador_mitigacao,
    RHC,
    RDC,
    CAUSAS,
    OCORRENCIAS,
    SUBESTACOES,
)


class TreeNode:
    """
    TreeNode of Tree object:
    """

    def __init__(self, data):
        self.data = data
        self.parent = None
        self.children = list()

    def __eq__(self, other):
        if isinstance(other, TreeNode):
            return self.data == other.data

    def __lt__(self, other):
        if isinstance(other, TreeNode):
            return self.data < other.data

    def __gt(self, other):
        if isinstance(self, other):
            return self.data > other.data

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.data})"

    def __str__(self) -> str:
        return f"{self.data}"

    def set_data(self, data):
        self.data = data

    def set_children(self, *children):
        for child in children:
            child.parent = self
            assert isinstance(child, TreeNode), f"{child} is not a TreeNode"
            self.children.append(child)
            self.children.sort()

    def get_children(self):
        return self.children

    def get_degree(self):
        return len(self.children)

    def set_parent(self, parent):
        assert isinstance(parent, TreeNode), f"{parent} is not a TreeNode"
        parent.set_children(self)

    def get_parent(self):
        return self.parent

    def is_root(self):
        if self.parent is None:
            return True
        return False

    def is_leaf(self):
        if self.children:
            return False
        return True

    def get_level(self):
        if self.is_root():
            return 0
        return 1 + self.parent.get_level()

    def get_root(self):
        if self.is_root():
            return self
        p: TreeNode = self.get_parent()
        while bool(p.get_parent()):
            p = p.get_parent()
        return p

    def get_heritage(self) -> list:
        node = self
        heritage = []

        while not node.is_root():
            heritage.append(node.parent)
            node = node.parent

        return heritage

    def print_tree(self, level = 0) -> None:
        spaces = "|   " * level
        prefix = spaces + "|-- " if level else ""
        print(prefix + str(self.data))
        if self.children:
            for child in self.children:
                child.print_tree(level + 1)

    def find(self, data):
        """
        Encontra um nó baseado em seu dado dentro da árvore
        """
        if self.data == data:
            return self
        for child in self.children:
            node = child.find(data)
            if node:
                return node
        return None

    def level_order_traversal(self):
        """
        Retorna todos os Nós a jusante do nó em uma lista
        """
        queue = [self]
        visited = []
        while queue:
            n = len(queue)
            while n > 0:
                node = queue.pop(0)
                visited.append(node)
                for i in range(len(node.children)):
                    queue.append(node.children[i])
                n -= 1
        return visited

    def depth_first_traversal(self, visited = []):
        if self in visited:
            return visited
        visited.append(self)
        if self.children:
            for child in self.children:
                child.depth_first_traversal(visited)
        return visited

class Chave(TreeNode):
    """
    Representa uma chave do sistema elétrico de distribuição de média tensão.
    A representação de uma chave é feita usando uma string composta pela sigla
    simo da região onde a chave se encontra, e então o código da chave.
    """

    def __init__(self, sigla_simo: str, codigo: int):
        super().__init__(f"{sigla_simo.upper()}_{codigo}")
        self.sigla_simo = str(sigla_simo).upper()
        self.codigo = int(codigo)
        self.ucs = RDC.loc[RDC["Chave"] == str(self)][
            "Consumidores a jusante"
        ].sum()
        self.dic = self.lista_ocorrencias["DIC"].sum()
        self.fic = self.lista_ocorrencias["QTDE UC EQPTO INTERROMPIDA"].sum()
        self.ocorrencias = self.lista_ocorrencias.shape[0]

    def __str__(self):
        """
        Retorna uma string com o nome da chave quando o objeto chave é chamado como string.
        """
        return f"{self.sigla_simo}_{self.codigo}"
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.sigla_simo}, {self.codigo})"

    @property
    def tipo(self) -> str:
        """
        Define o tipo da chave baseado no seu código.
        """
        codigo = self.codigo
        try:
            return RDC.loc[RDC["Chave"] == str(self)]["Tipo"].item()
        except Exception:

            if 1 <= codigo < 100:
                return "Chave Tripolar Sem Corte Vsível"
            elif 100 <= codigo < 200:
                return "CD"
            elif 200 <= codigo < 300 or 85000 <= codigo < 86000:
                return "FU"
            elif 300 <= codigo < 400:
                return "Regulador de Tensão"
            elif 400 <= codigo < 500:
                return "Chave Tripolar com Corte Visível"
            elif 500 <= codigo < 600 or 86500 <= codigo < 87000:
                return "RA"
            elif 600 <= codigo < 800 or 82000 <= codigo < 83000:
                return "RA"
            elif 800 <= codigo < 2900 or 84000 <= codigo < 85000:
                return "Chave Faca Unipolar - Abertura com Carga"
            elif 2900 <= codigo < 3000:
                return "Chave Faca Unipolar - Abertura sem Carga"
            elif (
                3000 <= codigo < 5000
                or 80000 <= codigo < 82000
                or 87000 <= codigo < 89000
            ):
                return "FU"
            elif 5000 <= codigo < 70000:
                return "FU"
            elif 70000 <= codigo < 80000:
                return "FU"
            elif 85200 <= codigo < 86000:
                return "Chave Faca de Ramal Particular"
            elif 83000 <= codigo < 84000:
                return "Chave Base Fusível com Lâmina Seccionadora - Abertura com Carga"
            elif 86000 <= codigo < 86500:
                return "DJ PVO"
            elif 89000 <= codigo < 100000:
                return "Reserva Técnica"
            else:
                raise ValueError(
                    f"códgio {codigo} está fora da faixa numérica expecificada pelo Manual de Procedimentos"
                )

    @property
    def lista_ocorrencias(self) -> pd.DataFrame:
        return OCORRENCIAS.loc[
            (OCORRENCIAS["REGIONAL"] == simo_to_code(self.sigla_simo))
            & (OCORRENCIAS["EQPTO.RESPONSAVEL"] == self.codigo)
        ]

    def set_dic(self, value : float = 0) -> float:
        """
        Altera o valor o DIC da chave.
        """
        if value >= 0:
            self.dic = value
            return
        
    def dic_futuro(self) -> float:
        """
        Dic das ocorrencias referidas a chave vezes seu fator de redução
        """
        if self.tipo in ["RA", "TS"]:
            return self.dic

        dic = 0.0
        for row in self.lista_ocorrencias.itertuples():
            reducao = CAUSAS.loc[CAUSAS["CODIGO"] == getattr(row, "CAUSA")][
                "MITIGACAO POR RA"
            ].item()
            dic += getattr(row, "DIC") * (1 - reducao)
        return dic

    def set_fic(self, value) -> int:
        """
        Altera o valor do FIC da chave. 
        """
        if value >= 0:
            self.fic = value
            return

    def dic_acumulado(self) -> float:
        """
        Calcula o dic acumulado a jusante da chave (a partir dela até o final do ramo), somando o dic de cada chave.
        """
        lista_dic = []
        for node in self.depth_first_traversal():
            if not isinstance(node, Chave):
                continue
            lista_dic.append(node.dic)
        return round(sum(lista_dic), 2)

    def fic_acumuladro(self) -> float:
        """
        Calcula a soma de consumidores desligados a jusante da chave no periodo do relatório
        """
        lista_fic = []
        for chave in self.chaves_jusante():
            lista_fic.append(chave.fic())

    def chaves_jusante(self):
        """
        Encontra as chaves a jusante da referencia, excluindo as SEDs e suas chaves.
        """
        lista_objetos = self.depth_first_traversal()
        for obj in lista_objetos:
            if isinstance(obj, (Subestacao, Alimentador)):
                for x in obj.depth_first_traversal():
                    lista_objetos.remove(x)
        return lista_objetos

    def dic_acumulado_futuro(self) -> float:
        """
        Calcula o dic acumulado após a substituição da chave por chave religadora. se a chave referencia já for do tipo religadora,
        então o dic acumulado mitigado será o mesmo que o dic acumulado.

        nessa função foi considerada uma sensibilidade de 3, ou seja, ela atuara caso a falta ocorra no trecho entre a chave de referencia e 3 chaves em cascata.

        """
        lista_dic_mitigavel = []
        queue = self.chaves_jusante()
        visited = []

        for node in queue:
            if node in visited:
                continue
            if not isinstance(node, Chave):
                """
                Band-Aid, caso surja algum disjuntor de transformador ou algo do tipo, que ainda não consigo identificar no RHC
                """
                visited.append(node)
                continue
            if node.tipo in ["TS", "RA"]:
                """
                Adicionar a lista os valores integrais de dic das chaves a jusante da chave religadora, e de suas filhas, e removelas da lista.
                """
                lista_dic_mitigavel.append(node.dic_acumulado())
                for item in node.chaves_jusante():
                    visited.append(item)
                continue
            if (node.get_level() - self.get_level()) > 2:
                lista_dic_mitigavel.append(node.dic)
                # após o terceiro nivel, o valor do dic é o integral.
                visited.append(node)
                continue
            lista_dic_mitigavel.append(node.dic_futuro())
            visited.append(node)
        return round(sum(lista_dic_mitigavel), 2)

    def tempo_interrupcao(self) -> float:
        return self.lista_ocorrencias["DURACAO"].sum()

    def tempo_interrupcao_mitigado(
        self,
        mitigacao: Literal[
            "MITIGACAO POR RA",
            "MITIGACAO TA MESMA SE",
            "MITIGACAO TA SE DIFERENTE",
        ],
    ) -> float:
        tempo_total = 0.0
        for row in self.lista_ocorrencias.itertuples():

            tempo_total += getattr(row, "DURACAO") * (
                1 - multiplicador_mitigacao(row, mitigacao)
            )
        return tempo_total / 60

    def ucs_jusante(self) -> int:
        consumidores = RDC.loc[RDC["Chave"] == str(self)][
            "Consumidores a jusante"
        ].sum()
        if consumidores:
            return consumidores
        consumidores = 0
        for chave in self.chaves_jusante():
            consumidores += RDC.loc[RDC["Chave"] == str(self)]["Consumidores a jusante"].sum()
        return consumidores

    def ucs_entre(self, other) -> int:
        if self.get_level() > other.get_level():
            return other.ucs_jusante() - self.ucs_jusante()
        return self.ucs_jusante() - other.ucs_jusante()

    def chaves_montante(self, *, to_root : bool = True) -> list:
        nodes = self.get_heritage()
        chaves_montante = []
        node: TreeNode
        for node in nodes:
            if isinstance(node, Alimentador) and not to_root:
                return chaves_montante
            if node.get_level() == 3:
                return chaves_montante
            chaves_montante.append(node)
        

    def dic_montante(self):
        """
        Somatório do dos dics das chaves a montande da chave de referencia.
        """
        chave : Chave
        dic_montante = 0.0
        for chave in self.chaves_montante():
            dic_montante += chave.dic
        return dic_montante


    # O Multiplicador de mitigacao no caso de transferencia de carga, não diz respeito ao tempo, mas sim a um dado estatistico

    def dic_ta(self, tipo = Literal["MITIGACAO TA MESMA SE", "MITIGACAO TA SE DIFERENTE"]):
        """
        A transferencia automatica de carga se da entre alimentadores de subestacoes diferentes ou iguais, esses casos tem multiplicadores de mitigacao dife
        """
        chaves = self.chaves_montante()
        if not chaves:
            return 0.00
        chave: Chave
        dic_ta = 0.00
        for chave in chaves:
            # multiplicar a duracao da interrupcao pelo ucs a jusante da chave - self.ucs * (1 - multiplicador)
            dic_ta = (
                chave.tempo_interrupcao()
                - chave.tempo_interrupcao_mitigado(tipo)
            ) * (chave.ucs_entre(self))
        return dic_ta

    def get_nucleo(self) -> TreeNode:
        for parent in self.get_heritage():
            if isinstance(parent, Nucleo):
                return parent

    def get_subestacao(self) -> TreeNode:
        for parent in self.get_heritage():
            if isinstance(parent, Subestacao):
                return parent


    def get_alimentador(self) -> TreeNode:
        for parent in self.get_heritage():
            if isinstance(parent, Alimentador):
                return parent

    def dec(self) -> float:
        alm: Alimentador = self.get_alimentador()
        ucs_alm = alm.ucs()
        if ucs_alm:
            return round(self.dic / ucs_alm, 2)
        return 0.00

    def dec_futuro(self) -> float:
        alm: Alimentador = self.get_alimentador()
        ucs_alm = alm.ucs()
        if ucs_alm:
            return round(self.dic_futuro() / ucs_alm, 2)
        return 0.00

    def dec_acumulado(self) -> float:
        alm: Alimentador = self.get_alimentador()
        ucs_alm = alm.ucs()
        if ucs_alm:
            return round(self.dic_acumulado() / ucs_alm, 2)
        return 0.00

    def dec_acumulado_futuro(self) -> float:
        alm: Alimentador = self.get_alimentador()
        ucs_alm = alm.ucs()
        if ucs_alm:
            return round(self.dic_acumulado_futuro() / ucs_alm, 2)
        return 0.00


class Alimentador(TreeNode):
    """
    Representa um alimentador do sistema elétrico de distribuição em média tensão.
    Um alimentador possui um conjunto de chaves organizadas em hierarquia, e um CHI total.
    """

    def __init__(self, nome: str):
        super().__init__(nome)
        self.nome = nome

    def __str__(self) -> str:
        return f"{self.nome}"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.nome})"

    def ucs(self) -> int:
        """
        Depende do relatórios de chaves estar atualizado.
        """

        chaves = self.get_children()
        consumidores = 0
        for chave in chaves:
            if isinstance(chave, Chave):
                consumidores += chave.ucs_jusante()
        return consumidores

    def dic(self) -> float:
        chaves = self.get_children()
        _dic = 0.0
        for chave in chaves:
            if isinstance(chave, Chave):
                _dic += chave.dic_acumulado()
        return _dic

    def dec(self) -> float:
        return self.dic() / self.ucs()


class Subestacao(TreeNode):
    """
    Represesta uma subestação do sistema elétrico de distribuição em média tensão
    """

    def __init__(self, nome: str):
        super().__init__(nome)
        self.nome = nome

    def __str__(self) -> str:
        return self.nome

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.nome})"

    def ucs(self) -> int:
        alimentadores = self.get_children()
        consumidores = 0
        for alimentador in alimentadores:
            if isinstance(alimentador, Alimentador):
                consumidores += alimentador.ucs()
        return consumidores

    def dic(self) -> float:
        alimentadores = self.get_children()
        _dic = 0.0
        for alimentador in alimentadores:
            if isinstance(alimentador, Alimentador):
                _dic += alimentador.dic()
        return _dic

    def dec(self) -> float:
        return self.dic() / self.ucs()


class Nucleo(TreeNode):
    """
    Representa todo o Núcleo ou unidade da empresa.
    """

    def __init__(self, nome: str):
        nome = nome.upper()
        super().__init__(nome)
        self.nome = nome

    def __str__(self) -> str:
        return self.nome

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.nome})"

    def ucs(self) -> int:
        subestacoes = self.get_children()
        consumidores = 0
        for subestacao in subestacoes:
            if isinstance(subestacao, Subestacao):
                consumidores += subestacao.ucs()

    def dic(self) -> float:
        subestacoes = self.get_children()
        _dic = 0.0
        for subestacao in subestacoes:
            if isinstance(subestacao, Subestacao):
                _dic += subestacao.dic()
        return _dic

    def dec(self) -> float:
        return self.dic() / self.ucs()


class Empresa(TreeNode):
    def __init__(self, nome="CELESC"):
        super().__init__(nome)
        self.nome = nome

    def __str__(self) -> str:
        return self.nome

    def ucs(self) -> int:
        nucleos = self.get_children()
        consumidores = 0
        for nucleo in nucleos:
            if isinstance(nucleo, Nucleo):
                if nucleo.ucs():
                    consumidores += nucleo.ucs()
        return consumidores

    def dic(self) -> float:
        nucleos = self.get_children()
        _dic = 0.0
        for nucleo in nucleos:
            if isinstance(nucleo, Nucleo):
                _dic += nucleo.dic()
        return _dic

    def dec(self) -> float:
        return self.dic() / self.ucs()


def CriarRede() -> Empresa:
    """
    Representa as regiões, subestações, alimentadores e suas respectivas chaves usando uma estrutura de árvore e nós, comumente chamada de "Tree-TreeNode data structure"

    """
    root = Empresa()
    lista_nucleos = []
    nomes_nucleos = []
    for nucleo in list(SUBESTACOES.keys()):
        nomes_nucleos.append(nucleo)
        nucleo = Nucleo(nucleo)
        nucleo.set_parent(root)
        lista_nucleos.append(nucleo)
        
    parent = root
    curdepth = 1
    for row in RHC.itertuples():
        depth = 1
        for value in row[1:]:
            depth += 1
            if  value == "\x1a":
                return root
            if isinstance(value, float):
                continue
            else:
                break
        while curdepth >= depth:
            parent = parent.parent
            curdepth -= 1

        if depth == 2:  # Subestacoes
            data = value.split(" ")[0]
            node = Subestacao(data)
            nome_nucleo = encontrar_nucleo(node.nome)
            if nome_nucleo:
                node.set_parent(lista_nucleos[nomes_nucleos.index(nome_nucleo)]) if node else None
            else:
                node.set_parent(root)


        elif depth == 3:  # Alimentador
            data = value.split(" ")[0]
            node = Alimentador(data)
            node.set_parent(parent)

        else:  # Chaves
            if "BT " in value or "TT-" in value:
                data = value.split(" ")[0]
                node = Subestacao(data)
                node.set_parent(parent)
            elif "DJ_" in value:
                data = value.split(" ")[0].removeprefix("DJ_").removesuffix("_FICT")
                node = Alimentador(data)
                node.set_parent(parent)
                
            else:
                sigla_simo, codigo = value.split()[0].split("_")
                node = Chave(sigla_simo, codigo)
                node.set_parent(parent)
                
        parent = node
        curdepth += 1
    return root
