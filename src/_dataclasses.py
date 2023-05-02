#---------------------------------------
# Autor:    Ruan Carlo Weiers Britzke
# Lotação:  DPEP/DVPE
# Data:     30/03/2023
#---------------------------------------

from typing import Literal, Dict
from src._database import (
    pd,
    regionais,
    encontrar_nucleo,
    encontrar_se,
    multiplicador_mitigacao,
    RHC,
    RDC,
    SUBESTACOES,
    CAUSAS,
    OCORRENCIAS,
)

RDC_TIPOS: Dict[str, str] = dict(RDC[["Chave", "Tipo"]].values)

SECCIONADORA = 'CD'
FUSIVEL = 'FU'
RELIGADOR_AUTOMATICO = 'RA'
TRIP_SAVER = 'TS'



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

    def __repr__(self) -> str:
        """
        Retorna uma representação em string do  objeto Nó
        """
        return f"{self.__class__.__name__}({self.data})"

    def __str__(self) -> str:
        """
        Retorna uma representação em string dos dados armazenados no nó
        """
        return f"{self.data}"

    def set_children(self, *children):
        """
        Adiciona nós filhos ao nó
        """
        for child in children:
            child.parent = self
            assert isinstance(child, TreeNode), f"{child} is not a TreeNode"
            self.children.append(child)

    def set_parent(self, parent):
        """
        Seta o nó pai do Nó de referência.
        """

        assert isinstance(parent, TreeNode) or parent != None, f"{parent} is not a TreeNode"
        parent.set_children(self)

    @property
    def is_root(self):
        """
        Retorna True se Nó é raiz, caso contrario False
        """

        return self.parent is None

    def level(self):
        """
        Retorna o nível do Nó, 0 caso for raiz.
        """

        if self.is_root:
            return 0
        return 1 + self.parent.level()

    def get_root(self):
        """
        Retorna a raiz da estrutura TreeNode.
        """
        node = self
        while node.parent:
            node = node.parent
        return node

    def heritage(self) -> list:
        """
        Retorna uma lista dos ancestrais do Nó. Apartir da raiz até o nó de referência.
        """
        node = self
        heritage = []
        while not node.is_root:
            heritage.insert(0, node.parent)
            node = node.parent
        return heritage

    def order(self) -> int:
        return len(self.children)

    def print_tree(self, level = 0) -> None:
        """
        Imprime a estrutura hierarquica dos objetos salvos na Árvore.
        """
        spaces = "|   " * level
        prefix = spaces + "|-- " if level else ""
        if isinstance(self, Chave):
            print(prefix + str(self.data) + " " + self.tipo)
        elif self.children:
            print(prefix + str(self.data))
        if self.children:
            for child in self.children:
                child.print_tree(level + 1)

    def find(self, data):
        """
        Encontra um nó baseado
        em seu dado 
        dentro da árvore. 
        Procura em profundidade
        primeiro. 
        """
        if self.data == data:
            return self
            
        for child in self.children:
            found = child.find(data)
            if found:
                return found
        return None

    def depth_first_traversal(self, visited = None):
        """
        Travessia em profundidade primeiro.
        Retorna todos os nó a jusante do nó de referência,
        percorrendo toda a profundidade do ramo antes de ir
        para o próximo.
        """
        if visited is None:
            visited = []
        visited.append(self)
        if self.children:
            for child in self.children:
                child.depth_first_traversal(visited)
        return visited

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
            return RDC_TIPOS[str(self)]
        except Exception:

            if 1 <= codigo < 200 or 300 <= codigo < 500 or 800 <= codigo < 3000 or 83000 <= codigo < 85000 or 85200 <= codigo < 86000:
                return SECCIONADORA
            elif 200 <= codigo < 300 or 3000 <= codigo <  82000 or 87000 <= codigo < 89000 or 85000 <= codigo < 86500:
                return FUSIVEL
            elif 500 <= codigo < 800 or 82000 <= codigo < 83000  or 86500 <= codigo < 87000:
                return RELIGADOR_AUTOMATICO
            elif 89000 <= codigo < 100000:
                return TRIP_SAVER
            else:
                raise ValueError(
                    f"códgio {codigo} está fora da faixa numérica expecificada pelo Manual de Procedimentos"
                )

    @property
    def ocorrencias(self) -> pd.DataFrame:
        """
        Retorna o relatório de ocorrencias 1025 filtrado
        para todas a chaves de referencia. 
        """
        return OCORRENCIAS.loc[
            (OCORRENCIAS["REGIONAL"] == regionais(self.sigla_simo))
            & (OCORRENCIAS["EQPTO.RESPONSAVEL"] == self.codigo)
        ]

    @property
    def qtd_ocorrencias(self):
        return self.ocorrencias.shape[0]

    @property
    def ocorrencias_jusante(self) -> pd.DataFrame:
        """
        Retorna o relatório de ocorrencias 1025 filtrado
        para todas as chaves a jusante da chave de referência. 
        """
        df = pd.DataFrame()
        for chave in self.chaves_jusante():
            df = pd.concat([df, chave.ocorrencias], ignore_index= True)
        return df

    @property
    def ocorrencias_montante(self) -> pd.DataFrame:
        """
        Retorna o relatório de ocorrencias 1025 filtrado
        para todas as chaves a jusante da chave de referência.
        """
        df = pd.DataFrame()
        for chave in self.chaves_montante():
            df = pd.concat([df, chave.ocorrencias], ignore_index= True)
        return df

    @property
    def fic(self):
        """
        Retorna a frequencia de interrupção vezes consumidor da chave.
        """
        return self.ocorrencias["QTDE UC EQPTO INTERROMPIDA"].sum()

    @property
    def ucs(self):
        return RDC.loc[RDC["Chave"] == str(self)][
            "Consumidores a jusante"
        ].sum()

    @property
    def dic(self):
        return self.ocorrencias["DIC"].sum()
    
    @property
    def dic_pos_rl(self) -> float:
        """
        Dic das ocorrencias referidas a chave vezes seu fator de redução
        """
        if self.tipo in [RELIGADOR_AUTOMATICO, TRIP_SAVER]:
            return self.dic
        dic = 0.0
        for row in self.ocorrencias.itertuples():
            reducao = CAUSAS.loc[CAUSAS["CODIGO"] == getattr(row, "CAUSA")][
                "MITIGACAO POR RA"
            ].item()
            dic += getattr(row, "DIC") * (1 - reducao)
        return dic

    def chaves_jusante(self):
        """
        Encontra as chaves a jusante da referencia, excluindo as SEDs e suas chaves.
        """
        lista_objetos = self.depth_first_traversal()
        for node in lista_objetos:
            if isinstance(node, (Subestacao, Alimentador)):
                for x in node.depth_first_traversal():
                    lista_objetos.remove(x)
        return lista_objetos

    def dic_jusante(self) -> float:
        """
        Calcula o dic acumulado a jusante da chave (a partir dela até o final do ramo), somando o dic de cada chave.
        """
        return sum([chave.dic for chave in self.chaves_jusante()])

    def dic_jusante_pos_rl(self) -> float:
        """
        Calcula o dic acumulado após a substituição da chave por chave religadora. se a chave referencia já for do tipo religadora,
        então o dic acumulado mitigado será o mesmo que o dic acumulado. Nessa função foi considerada uma sensibilidade de 3, ou seja,
        ela atuara caso a falta ocorra no trecho entre a chave de referencia e 3 chaves em cascata.
        """
        return sum([chave.dic_pos_rl if (chave.level() - self.level()) < 2 else chave.dic for chave in self.chaves_jusante()])

    def fic_jusante(self) -> float:
        """
        Retorna a frequência de interrupção do "conjunto" das chaves a justante da referencia.
        """
        return sum([chave.fic for chave in self.chaves_jusante()])

    def chaves_montante(self) -> list:
        """
        Retorna a lista de chaves entre a substação e a chave de referência.
        """
        chaves_montante = []
        node: TreeNode
        for node in reversed(self.heritage()):
            if isinstance(node, Alimentador):
                return list(reversed(chaves_montante))
            chaves_montante.append(node)

    def dic_montante(self):
        """
        Somatório do dos dics das chaves a montande da chave de referencia.
        """
        return sum([chave.dic for chave in self.chaves_montante()])


    def dic_montante_pos_ta(self, *, tipo_ta: Literal["MESMA SE", "SE DIFERENTE"] = "MESMA SE", other=None) -> float:
        """
        Retorna DIC montante a chave caso esta fosse uma religadora em transferencia automatica de carga.
        CHI é calculado somando os valores de duração de interrupção multiplicados pelas ucs afetadas.
        
        """
        chaves_montante = self.chaves_montante()
        if not chaves_montante:
            return 0
        ucs_chave = self.ucs
        chi_ta = 0
        for chave_montante in chaves_montante:
            for row in chave_montante.ocorrencias.itertuples(): 
                ucs_chave_montante = getattr(row, '_10')
                mitigacao = multiplicador_mitigacao(row, f"MITIGACAO TA {tipo_ta}")
                duracao = getattr(row, "DURACAO")
                if ucs_chave_montante >= ucs_chave:
                    chi_ta += (ucs_chave_montante - mitigacao*ucs_chave)*duracao
                else: 
                    chi_ta += getattr(row, "DIC")
        if other is None:
            return chi_ta
        if not isinstance(other, Chave) and other is not None:
            raise TypeError("Other must be Chave or None")
        if self.subestacao == other.subestacao:
            return self.dic_montante_pos_ta(tipo_ta="MESMA SE") + other.dic_montante_pos_ta(tipo_ta="MESMA SE")
        return self.dic_montante_pos_ta(tipo_ta="SE DIFERENTE") + other.dic_montante_pos_ta(tipo_ta="SE DIFERENTE")

    @property
    def alimentador(self):
        """
        Retorna o Alimentador da Chave
        """
        for parent in reversed(self.heritage()):
            if isinstance(parent, Alimentador):
                return parent

    @property
    def subestacao(self):
        """
        Retorna a SE da Chave
        """
        for parent in reversed(self.heritage()):
            if isinstance(parent, Subestacao):
                return parent

    @property
    def nucleo(self):
        """
        Retorna o Núcleo da Chave
        """
        for parent in self.heritage():
            if isinstance(parent, Nucleo):
                return parent

class Alimentador(TreeNode):
    """
    Representa um alimentador do sistema elétrico de distribuição em média tensão.
    Um alimentador possui um conjunto de chaves organizadas em hierarquia.
    """

    def __init__(self, nome: str):
        super().__init__(nome)
        self.nome = nome

    def __str__(self) -> str:
        return f"{self.nome}"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.nome})"

    @property
    def SED(self):
        for x in self.depth_first_traversal():
            if x.__class__.__name__ == "Subestacao":
                return x
        return None
        
    @property
    def chaves(self):
        """
        Retorna todas as chaves do alimentador em ordem de nivel.
        """
        chaves = []
        child: Chave
        for child in self.children:
            chaves.extend(child.chaves_jusante())
        return chaves

    @property
    def ucs(self) -> int:
        """
        Número de unidades consumidoras atendidas pelo Alimentador.
        """
        ucs = []
        chaves = self.chaves
        for chave in chaves:
            if chave.ucs:
                ucs.append(chave.ucs)
                for x in chave.chaves_jusante():
                    chaves.remove(x)
        return sum(ucs)        
            
    @property
    def ocorrencias(self):
        return OCORRENCIAS.loc[(OCORRENCIAS["SUBESTACAO"] == encontrar_se(self.parent.nome, "CÓD._SE"))
         & (OCORRENCIAS["ALIMENTADOR"] == int(self.nome[3:]))]

    @property
    def dic_1025(self):
        return self.ocorrencias["DIC"].sum()

    @property
    def dic(self) -> float:
        """
        Chi total do Alimentador
        """
        return sum([chave.dic for chave in self.chaves])

    @property
    def dec(self) -> float:
        """
        DEC do Alimentador. 
        """
        return self.dic / self.ucs

    @property
    def dec_1025(self):
        return self.dic_1025 / self.ucs

    @property
    def qtd_chaves(self):
        """
        Retorna número de chaves do alimentador.
        """
        return len(self.chaves)
    
    def chaves_candidatas(self) -> list:
        """
        Retorna lista das chaves que são possiveis de trocar por religador trifásico.
        """
        candidatas = []
        chaves = self.chaves
        chave: Chave
        # itera a partir das chaves mais distantantes em hierarquia da saida do alimentador
        for chave in chaves:
            if not isinstance(chave, Chave):
                continue
                # Garante que as a lista tenha apenas chaves, sem nenhuma SED.
            if chave.tipo in [RELIGADOR_AUTOMATICO, TRIP_SAVER]:
                continue
                # Descarta chaves que já são religadoras, ou que não podem ser substituidas por chave religadora
            if chave.tipo == FUSIVEL and chave.parent.tipo == FUSIVEL:
                continue
                # Descarta Ramais
            candidatas.append(
                chave) if chave not in candidatas else None
            # Adiciona a chave a lista se ela já não estiver na lista.
        return candidatas

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
    def chaves(self) -> list:
        """
        Retorna uma lista com todas as chaves pertencentes a um alimentador. 
        """
        lista = []
        for alm in self.children:
            if isinstance(alm, Alimentador):
                lista.extend(alm.chaves)
        return lista

    @property
    def qtd_chaves(self):
        return len(self.chaves)

    @property
    def ucs(self) -> int:
        """
        Número de unidades consumidoras da SE.
        """
        return sum([alm.ucs for alm in self.children])

    @property
    def ocorrencias(self):
        return OCORRENCIAS.loc[OCORRENCIAS["SUBESTACAO"] == encontrar_se(self.nome, "CÓD._SE")]

    @property
    def dic_1025(self):
        return self.ocorrencias["DIC"].sum()

    @property
    def dic(self) -> float:
        """
        DIC da SE.
        """
        return sum([chave.dic for chave in self.chaves])

    @property
    def dec(self) -> float:
        """
        DEC da SE.
        """
        return self.dic / self.ucs

    @property
    def dec_1025(self) -> float:
        return self.dic_1025 / self.ucs

    def chaves_candidatas(self) -> list:
        """
        Retorna lista de chaves candidatas para substituição substituição por RL Trifásico na SE. 
        """
        return [chave for alm in self.children for chave in alm.chaves_candidatas()]


    def chaves_candidatas_ts(self) -> list:
        """
        Retorna lista de chaves candidatas para substituição substituição por RL Monofásico na SE. 
        """
        return [chave for alm in self.children for chave in alm.chaves_candidatas_ts()]

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

    @property
    def subestacoes(self):
        subestacoes = []
        for node in self.depth_first_traversal():
            subestacoes.append(node) if isinstance(node, Subestacao) and node.children else None
        return subestacoes

    @property
    def chaves(self):
        chaves = []
        se: Subestacao
        for se in self.subestacoes:
            chaves.extend(se.chaves)
        return chaves

    @property
    def ocorrencias(self):
        return OCORRENCIAS[OCORRENCIAS["REGIONAL"] == regionais(self.nome, tipo = "Núcleo")]

    @property
    def qtd_chaves(self):
        return len(self.chaves)
    
    @property
    def ucs(self):
        return sum([se.ucs for se in self.children])
    
    @property
    def dic(self):
        return sum([chave.dic for chave in self.chaves])

    @property
    def dic_1025(self):
        return self.ocorrencias["DIC"].sum()

    @property
    def dec(self):
        return self.dic / self.ucs

    @property
    def dec_1025(self):
        return self.dic_1025 / self.ucs


    def chaves_candidatas(self) -> list:
        """
        Retorna lista de chaves candidatas para substituição substituição por RL Trifásico na SE. 
        """
        return [chave for se in self.subestacoes for chave in se.chaves_candidatas()]


    def chaves_candidatas_ts(self) -> list:
        """
        Retorna lista de chaves candidatas para substituição substituição por RL Monofásico na SE. 
        """
        return [chave for se in self.subestacoes for chave in se.chaves_candidatas_ts()]

class Empresa(TreeNode):
    def __init__(self, nome="CELESC"):
        super().__init__(nome)
        self.nome = nome

    def __str__(self) -> str:
        return self.nome

    @property
    def nucleos(self):
        nucleos = []
        for node in self.depth_first_traversal():
            nucleos.append(node) if isinstance(node, Nucleo) and node.children else None
        return nucleos

    @property
    def chaves(self):
        chave = []
        for nucleo in self.nucleos:
            chave.extend(nucleo.chaves)
        return chave

    @property
    def qtd_chaves(self):
        return len(self.chaves)

    @property
    def ucs(self):
        return sum([x.ucs for x in self.nucleos])
    
    def chaves_candidatas(self) -> list:
        """
        Retorna lista de chaves candidatas para substituição substituição por RL Trifásico na SE. 
        """
        return [chave for nu in self.nucleos for chave in nu.chaves_candidatas()]

    def chaves_candidatas_ts(self) -> list:
        """
        Retorna lista de chaves candidatas para substituição substituição por RL Monofásico na SE. 
        """
        return [chave for nu in self.nucleos for chave in nu.chaves_candidatas_ts()]

def CriarRede() -> Empresa:
    """
    Cria a representação das regiões, subestações, alimentadores e suas
    respectivas chaves usando uma estrutura de árvore e nós.
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
