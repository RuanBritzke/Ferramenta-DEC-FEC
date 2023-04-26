from typing import Literal
import pandas as pd
import numpy as np
import tkinter as tk
from tkinter.filedialog import askopenfilenames
from src._constants import SUBESTACOES, REGIONAIS

pd.options.mode.chained_assignment = None

CAUSAS = pd.read_pickle(
    "base/CAUSAS", compression={'method': "gzip", 'compresslevel': 1, 'mtime': 1})

RHC = pd.read_pickle(
    "base/RHC", compression={'method': "gzip", 'compresslevel': 1, 'mtime': 1})

RDC = pd.read_pickle(
    "base/RDC", compression={'method': "gzip", 'compresslevel': 1, 'mtime': 1})

OCORRENCIAS = pd.read_pickle(
    "base/OCORRENCIAS", compression={'method': "gzip", 'compresslevel': 1, 'mtime': 1})

SES = pd.read_pickle(
    "base/CODIGOS_SE", compression={'method': "gzip", 'compresslevel': 1, 'mtime': 1})

def encontrar_se(entry: str | int, onde="SIGLA_SE"):
    """
    Função que identifica a subestacao baseada no codigo da mesma.
    """
    local = get_row(SES, entry), onde
    return SES.at[(local)]

def selecionar_arquivos(mensagem):
    root = tk.Tk()
    root.withdraw()
    filenames = askopenfilenames(
        title=f"Selecione os arquivos {mensagem}.",
    )
    return filenames

def concatenar_df(*args):
    arg: pd.DataFrame
    if len(args) == 1:
        return args[0]
    df = args[0]
    for arg in args[1:]:
        df = pd.concat([df, arg], ignore_index=True)
    return df

def get_column(df: pd.DataFrame, val: str) -> str:
    _, column = np.where(df.to_numpy() == val)
    return next(iter(df.columns[column]), 0)

def get_row(df: pd.DataFrame, val: str) -> int:
    row, _ = np.where(df.to_numpy() == val)
    return next(iter(df.index[row]), 0)


def regionais(entry: str | int, tipo: Literal["Agência", "Sigla", "Núcleo", "Siglas SIMO", "Cidade"] = "Siglas SIMO"):
    """
    Usa especificamente a tabela de regionais.
    Função que identifica o tipo de entrada da região e traduz para o valor simo correspondente.
    """
    for key, value in REGIONAIS[tipo].items():
        if value == entry:
            return key
    return None

def encontrar_se(entry: str | int, onde="SIGLA_SE"):
    """
    Função que identifica a subestacao baseada no codigo da mesma.
    """
    local = get_row(SES, entry), onde
    return SES.at[(local)]

def encontrar_nucleo(entry: str):
    for key, _ in SUBESTACOES.items():
        if entry in SUBESTACOES[key].values():
            return key

def multiplicador_mitigacao(
    Codigo,
    tipo: Literal[
        "MULTIPLICADOR MITIGACAO POR RA",
        "MITIGACAO TA MESMA SE",
        "MITIGACAO TA SE DIFERENTE",
    ],
) -> float:
    return CAUSAS.loc[CAUSAS["CODIGO"] == getattr(Codigo, "CAUSA")][tipo].item()

def atualiazar_ocorrencias():
    arquivos = selecionar_arquivos("1025")
    if not arquivos:
        return
    print("Atualizando Relatório de Ocorrências 1025", end= "\r")
    OCORRENCIAS = pd.DataFrame()
    for arquivo in arquivos:
        temp = pd.read_csv(arquivo, sep=";", usecols=["DOCUMENTO", "REGIONAL", "SUBESTACAO", "ALIMENTADOR", "EQPTO.RESPONSAVEL", "DATA INICIO", "DATA FIM", "CAUSA", "DURACAO", "QTDE UC EQPTO INTERROMPIDA"])
        temp["DURACAO"] = temp["DURACAO"]/60
        temp["DIC"] = temp["QTDE UC EQPTO INTERROMPIDA"] * temp["DURACAO"]
        temp["DATA INICIO"] = temp["DATA INICIO"].apply(lambda x: x.split()[0])
        temp["DATA FIM"] = temp["DATA FIM"].apply(lambda x: x.split()[0])
        OCORRENCIAS = concatenar_df(OCORRENCIAS, temp)
    print("Relátorio de Ocorrências 1025 atualizado! ")
    OCORRENCIAS.to_pickle('base/OCORRENCIAS', compression={'method': "gzip", 'compresslevel': 1, 'mtime': 1})

def atualizar_relatorio_hierarquico_chaves():
    data_files = selecionar_arquivos("Relatório Hierarquico de Chaves")
    if not data_files:
        return 
    print("Atualizando Relatório Hierarquico de Chaves", end="\r")
    RHC = pd.DataFrame()
    for data_file in data_files:
        data_file_delimiter = ";"
        largest_column_count = 0
        with open(data_file, "r") as temp_f:
            lines = temp_f.readlines()
            for l in lines:
                column_count = len(l.split(data_file_delimiter)) + 1
                largest_column_count = (
                    column_count
                    if largest_column_count < column_count
                    else largest_column_count
                )
        column_names = [i for i in range(0, largest_column_count - 1)]
        RHC = concatenar_df(RHC, pd.read_csv(
            data_file, header=None, delimiter=data_file_delimiter, names=column_names, dtype=object
        ))
    RHC.drop(columns= 2, inplace = True)
    RHC.dropna(axis=0, how="all", inplace=True)
    print("Relatório Hierarquico de Chaves atualizado! ")
    # Limpa os disjuntores ficticios do RHC da segunda coluna do arquivo csv (importante para evitar bugs)
    RHC.to_pickle("base/RHC", compression={'method': "gzip", 'compresslevel': 1, 'mtime': 1})

def atualizar_relatorio_de_chaves():
    arquivos = selecionar_arquivos("Relatório de Chaves")
    if not arquivos:
        return
    print("Atualizando Relatório de Chaves", end="\r")
    RDC = pd.DataFrame()
    for arquivo in arquivos:
        temp = pd.read_csv(
            arquivo,
            sep=";",
            header=0,
            usecols=["Chave", "Tipo", "Consumidores a jusante"],
            encoding="latin-1"
        )
        temp["Consumidores a jusante"] = pd.to_numeric(
            temp["Consumidores a jusante"], errors="coerce", downcast="integer"
        )
        RDC = concatenar_df(RDC, temp)
    print("Relatório de Chaves atualizado! ")
    RDC.to_pickle("base/RDC",compression={'method': "gzip", 'compresslevel': 1, 'mtime': 1})

def importar_arquivos():
    atualiazar_ocorrencias()
    atualizar_relatorio_de_chaves()
    atualizar_relatorio_hierarquico_chaves()
