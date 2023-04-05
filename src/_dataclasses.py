#---------------------------------------
# Autor:    Ruan Carlo Weiers Britzke
# Lotação:  DPEP/DVPE
# Data:     30/03/2023
#---------------------------------------

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
        """
        Checa se data de dois Nós são iguais
        """
        return self.data == other.data

    def __lt__(self, other):
        """
        Checa se os dados de um Nó é menor que o outro
        """
        return self.data < other.data

    def __repr__(self) -> str:
        """
        Retorna uma representação em string do Nó
        """
        return f"{self.__class__.__name__}({self.data})"

    def __str__(self) -> str:
        """
        Retorna uma representação em string dos dados armazenados no nó
        """
        return f"{self.data}"

    def set_data(self, data):
        """
        Seta os dados do Nó
        """
        self.data = data

    def set_children(self, *children):
        """
        Adiciona nós filhos ao nó
        """
        for child in children:
            child.parent = self
            assert isinstance(child, TreeNode), f"{child} is not a TreeNode"
            self.children.append(child)
            self.children.sort()

    def get_children(self):
        """
        Retorna a lista de filhos do nó
        """
        return self.children

    def get_degree(self):
        """
        Retorna o grau do nó (número de filhos)
        """
        return len(self.children)

    def set_parent(self, parent):
        """
        Seta o nó pai do Nó de referência.
        """

        assert isinstance(parent, TreeNode) or parent != None, f"{parent} is not a TreeNode"
        parent.set_children(self)

    def get_parent(self):
        return self.parent

    @property
    def is_root(self):
        """
        Retorna True se Nó é raiz, caso contrario False
        """

        return self.parent is None

    @property
    def is_leaf(self):
        """
        Retorna True se o Nó é folha, caso contrario False
        """
        return not self.children


    def get_level(self):
        """
        Retorna o nível do Nó, 0 caso for raiz.
        """

        if self.is_root:
            return 0
        return 1 + self.parent.get_level()

    def get_root(self):
        """
        Retorna a raiz da estrutura TreeNode.
        """
        node = self
        while node.parent:
            node = node.parent
        return node

    def get_heritage(self) -> list:
        """
        Retorna uma lista dos ancestrais do Nó. Apartir da raiz até o nó de referência.
        """
        node = self
        heritage = []
        while not node.is_root:
            heritage.insert(0, node.parent)
            node = node.parent
        return heritage

    def print_tree(self, level = 0) -> None:
        """
        Imprime a estrutura hierarquica dos objetos salvos na Árvore.
        """
        spaces = "|   " * level
        prefix = spaces + "|-- " if level else ""
        if isinstance(self, Chave):
            print(prefix + str(self.data) + " " + self.tipo)
        else:
            print(prefix + str(self.data))
        if self.children:
            for child in self.children:
                child.print_tree(level + 1)

    def find(self, data):
        """
        Encontra um nó baseado em seu dado dentro da árvore. Procura em profundidade primeiro. 
        """
        if self.data == data:
            return self
            
        for child in self.children:
            found = child.find(data)
            if found:
                return found
        return None

    def bft(self):
        """
        Retorna todos os Nós a jusante do nó em uma lista, vasculhando todo o nivel primeiro.
        """
        queue = [self]
        visited = []
        while queue:
            node = queue.pop(0)
            visited.append(node)
            queue.extend(node.children)
        return visited


    def dft(self, visited = None):
        """
        Retorna todos os nó a jusante do nó de referência, percorrendo toda a profundidade do ramo antes de ir para o próximo.
        """
        if visited is None:
            visited = []
        visited.append(self)
        if self.children:
            for child in self.children:
                child.dft(visited)
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

    @property
    def ucs(self):
        return RDC.loc[RDC["Chave"] == str(self)][
            "Consumidores a jusante"
        ].sum()

    @property
    def dic(self):
        return self.lista_ocorrencias["DIC"].sum()
        
    @property
    def fic(self):
        return self.lista_ocorrencias["QTDE UC EQPTO INTERROMPIDA"].sum()

    @property
    def qtd_ocorrencias(self):
        return self.lista_ocorrencias.shape[0]
    
    @property
    def dic_pos_rl(self) -> float:
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

    def chaves_jusante(self):
        """
        Encontra as chaves a jusante da referencia, excluindo as SEDs e suas chaves.
        """
        lista_objetos = self.dft()
        for node in lista_objetos:
            if isinstance(node, (Subestacao, Alimentador)):
                for x in node.dft():
                    lista_objetos.remove(x)
        return lista_objetos

    def dic_acumulado(self) -> float:
        """
        Calcula o dic acumulado a jusante da chave (a partir dela até o final do ramo), somando o dic de cada chave.
        """
        return sum([chave.dic for chave in self.chaves_jusante()])


    def dic_acumulado_pos_rl(self) -> float:
        """
        Calcula o dic acumulado após a substituição da chave por chave religadora. se a chave referencia já for do tipo religadora,
        então o dic acumulado mitigado será o mesmo que o dic acumulado.
        nessa função foi considerada uma sensibilidade de 3, ou seja, ela atuara caso a falta ocorra no trecho entre a chave de referencia e 3 chaves em cascata.

        """
        return sum([chave.dic_pos_rl if (chave.get_level() - self.get_level()) < 2 else chave.dic for chave in self.chaves_jusante()])
        

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

    def ucs_entre(self, other) -> int:
        self: Chave
        other: Chave
        if self.get_level() > other.get_level():
            return other.ucs - self.ucs
        return self.ucs - other.ucs

    def chaves_montante(self) -> list:
        chaves_montante = []
        node: TreeNode
        for node in reversed(self.get_heritage()):
            if isinstance(node, Alimentador):
                return list(reversed(chaves_montante))
            chaves_montante.append(node)
        
    def dic_montante(self):
        """
        Somatório do dos dics das chaves a montande da chave de referencia.
        """
        return sum([chave.dic for chave in self.chaves_montante()])

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

    def get_alimentador(self):
        """
        Retorna o Alimentador da Chave
        """
        for parent in self.get_heritage():
            if isinstance(parent, Alimentador):
                return parent

    def get_subestacao(self):
        """
        Retorna a SE da Chave
        """
        for parent in self.get_heritage():
            if isinstance(parent, Subestacao):
                return parent

    def get_nucleo(self):
        """
        Retorna o Núcleo da Chave
        """
        for parent in self.get_heritage():
            if isinstance(parent, Nucleo):
                return parent


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

    @property
    def lista_chaves(self):
        """
        Retorna todas as chaves do alimentador em ordem de nivel.
        """
        lista_chaves = []
        child: Chave
        for child in self.children:
            lista_chaves.extend(child.chaves_jusante())
        return lista_chaves

    @property
    def ucs(self) -> int:
        """
        Número de unidades consumidoras atendidas pelo Alimentador.
        """
        chaves = self.lista_chaves
        consumidores = 0
        for chave in chaves:
            consumidores += chave.ucs
        return consumidores

    @property
    def dic(self) -> float:
        """
        Chi total do Alimentador
        """
        dic = 0.0
        chave: Chave
        for chave in self.children:
            dic += chave.dic_acumulado()
        return dic

    @property
    def dec(self) -> float:
        """
        DEC do Alimentador. 
        """
        return self.dic / self.ucs

    @property
    def lista_chaves(self):
        """
        Retorna todas as chaves do alimentador em ordem de nivel.
        """
        lista_chaves = []
        child: Chave
        for child in self.children:
            lista_chaves.extend(child.chaves_jusante())
        return lista_chaves

    @property
    def qtd_chaves(self):
        """
        Retorna número de chaves do alimentador.
        """
        return len(self.lista_chaves)
    
    def chaves_candidatas_rl(self) -> list:
        return

    def chaves_candidatas_ts(self) -> list:
        """
        Retorna as chaves candidatas a subistituição por religador monofásico no Alimentador.
        """
        lista_candidatas = []
        lista_chaves = self.lista_chaves
        chave: Chave
        # itera a partir das chaves mais distantantes em hierarquia da saida do alimentador
        for chave in reversed(lista_chaves):
            if not isinstance(chave, Chave):
                continue
                # Garante que as a lista tenha apenas chaves, sem nenhuma SED.
            if chave.tipo in ["TS", "RA", "CD"]:
                continue
                # Descarta chaves que já são religadoras, ou que não podem ser substituidas por chave religadora
            chaves_montante = chave.chaves_montante()
            tipos_montante = [x.tipo for x in chaves_montante]
            if "FU" in tipos_montante:
                # Checa se existem chaves FU a jusante
                # É possivel ganhar eficiencia removendo as chaves das lista de chaves do alimentador.
                # Não consegui fazer isso ainda
                for chave in reversed(chaves_montante):
                    if chave.tipo == "FU":
                       break
                       # seleciona a chave fúsivel a montante.
            if not chave.dic_acumulado():
                continue
                # Descarta chaves que não possuem CHI acumulado
            lista_candidatas.append(chave) if chave not in lista_candidatas else None
            # Adiciona a chave a lista se ela já não estiver na lista.
        return lista_candidatas



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

    @property
    def ucs(self) -> int:
        """
        Número de unidades consumidoras da SE.
        """
        alms = self.children
        consumidores = 0
        alm : Alimentador
        for alm in alms:
            consumidores += alm.ucs
        return consumidores

    @property
    def dic(self) -> float:
        """
        DIC da SE.
        """
        alms = self.children
        dic = 0.0
        alm: Alimentador
        for alm in alms:
            dic += alm.dic
        return dic

    @property
    def dec(self) -> float:
        """
        DEC da SE.
        """
        return self.dic / self.ucs

    def get_chaves_candidatas_ts(self) -> list:
        """
        Retorna lista de chaves candidatas para substituição substituição por RL Monofásico na SE. 
        """

        chaves_candidatas_ts = []
        alm: Alimentador
        for alm in self.children:
            chaves_candidatas_ts.extend(alm.get_chaves_candidatas_ts())
        return chaves_candidatas_ts

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


class Empresa(TreeNode):
    def __init__(self, nome="CELESC"):
        super().__init__(nome)
        self.nome = nome

    def __str__(self) -> str:
        return self.nome



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
