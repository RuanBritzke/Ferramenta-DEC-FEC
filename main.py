#---------------------------------------
# Autor:    Ruan Carlo Weiers Britzke
# Lotação:  DPEP/DVPE
# Data:     30/03/2023
#--------------------------------------- 
import os
import pandas as pd
from src._database import importar_arquivos, OCORRENCIAS
from src._dataclasses import CriarRede, Subestacao, Alimentador, Chave

CELESC = None

def filtro(entry: str):
    """
    Filtra entradas de usuario para que a os objetos estudados sejam coerentes com o estudo selecionado. 
    """
    while True:
        if entry == "":
            return False
        busca = CELESC.find(entry)
        if busca is None:
            print(f'Nenhum objeto "{entry}" encontrado na rede.\nTente novamente ou "Enter" para encerrar:')
            entry = input().upper()
            continue
        return busca

def continuar():
    print('\nPara continuar entre o próximo valor. Para encerrar o estudo pressione "ENTER".')
    entry = input().upper()
    return entry


def por_chave(chave: Chave):
    dic_acumulado = chave.dic_acumulado()
    dic_acumulado_pos_rl = chave.dic_acumulado_pos_rl()
    reducao_dic_acumulado = (
        round(100 * (1 - dic_acumulado_pos_rl / dic_acumulado), 2)
        if dic_acumulado
        else "NA"
    )
    chaves_nf = pd.DataFrame({
        "Núcleo / Unidade": str(chave.get_nucleo()),
        "Subestação": str(chave.get_subestacao()),
        "Alimentador": str(chave.get_alimentador()),
        "Chave": chave,
        "Unidade Consumidoras": chave.ucs,
        "DIC Chave [h*ucs]": chave.dic,
        "DIC Acumulado [h * ucs]": dic_acumulado,
        "DIC Estimado após substituição [h * ucs]": chave.dic_pos_rl,
        "DIC Acumulado estimado pós substituição [h * ucs]": dic_acumulado_pos_rl,
        "Redução DIC Acumulado estimada [%]": reducao_dic_acumulado,
    }, index = ['0'])

    print(chaves_nf.tail(1).transpose().to_string(header=None))
    if not os.path.exists("Estudo Ganho RLs NF.xlsx"):
        pd.DataFrame().to_excel("Estudo Ganho RLs NF.xlsx", index=False)
    with pd.ExcelWriter("Estudo Ganho RLs NF.xlsx", engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
        chaves_nf.to_excel(writer, index=False , sheet_name= "Estudo por Chave", startrow=writer.sheets["Estudo por Chave"].max_row, header= None)
    return

def por_alimentador(alm : Alimentador):
    print("Calculando valores, isso pode levar alguns segundos", end= "\r")
    df = pd.DataFrame(alm.get_chaves_candidatas_ts(), columns= ["Chave"])
    ucs = alm.ucs
    df["Redução DEC estimada [HI]"] = df["Chave"].apply(lambda x: (x.dic - x.dic_pos_rl)/ucs)
    df["Interrupções no periodo"] = df["Chave"].apply(lambda x: x.qtd_ocorrencias)
    df["Unidades consumidoras a jusante da Chave"] = df["Chave"].apply(lambda x: x.ucs)
    df = df[(df["Redução DEC estimada [HI]"]) != 0]

    if df.empty:
        print("Nenhuma chave encontrada para substituição!")

    df.sort_values(["Redução DEC estimada [HI]",
                    "Unidades consumidoras a jusante da Chave"], inplace=True, ascending=False)

    print(f"Unidades Consumidoras {alm}: {ucs}")
    print(df.to_string(index=False)) if not df.empty else None

    if not os.path.exists("Estudo Ganho RLs NF.xlsx"):
        pd.DataFrame().to_excel("Estudo Ganho RLs NF.xlsx", index=False)

    with pd.ExcelWriter("Estudo Ganho RLs NF.xlsx", engine = 'openpyxl', mode = 'a', if_sheet_exists='replace') as writer:
        df.to_excel(writer, index=False, sheet_name=f'Estudo Aliementador {str(alm)}')
    return

def por_subestacao(se: Subestacao):
    print("Calculando. Este processo pode levar alguns minutos.", end = '\r')
    df = pd.DataFrame(se.get_chaves_candidatas_ts(), columns= ["Chave"])
    ucs = se.ucs
    df["Alimentador"] = df["Chave"].apply(lambda x: x.get_alimentador())
    df = df[["Alimentador", "Chave"]]
    df["Redução DEC SE estimada [HI]"] = df.apply(lambda x:  (x["Chave"].dic - x["Chave"].dic_pos_rl)/ucs, axis=1)
    df["Redução DEC Alimentador estimada [HI]"] = df.apply(lambda x: (
        x["Chave"].dic - x["Chave"].dic_pos_rl)/x["Alimentador"].ucs, axis=1)
    df["Interrupções"] = df["Chave"].apply(lambda x: x.qtd_ocorrencias)
    df["UCs a jusante da Chave"] = df["Chave"].apply(lambda x: x.ucs)
    df = df[df["Redução DEC Alimentador estimada [HI]"] != 0]
    if df.empty:
        print("Nenhuma chave encontrada para substituição!")
    df.sort_values(["Redução DEC SE estimada [HI]",], inplace=True, ascending=False)
    print(f"Unidades Consumidoras {se}: {ucs}")
    print(df.to_string(index=False)) if not df.empty else None

    if not os.path.exists("Estudo Ganho RLs NF.xlsx"):
        pd.DataFrame().to_excel("Estudo Ganho RLs NF.xlsx", index=False)

    with pd.ExcelWriter("Estudo Ganho RLs NF.xlsx", engine= 'openpyxl', mode = 'a', if_sheet_exists= 'replace') as writer:
        df.to_excel(writer, index=False, sheet_name=f'Estudo Subestação {str(se)}')
    return

def estudo_ganho_rls_nf():
    """
    Gerenciador de estudos RL NF
    """
    print('Estudo Ganho RL NF:\nEntre com uma Chave, Alimentador, ou SE para começar a análise.\nPara voltar pressione "Enter"')
    entry = filtro(input().upper())
    while True:
        if not entry:
            return
        if entry.__class__.__name__ == "Chave":
            por_chave(entry)
            
        if entry.__class__.__name__ == "Alimentador":
            por_alimentador(entry)
            
        if entry.__class__.__name__ == "Subestacao":
            por_subestacao(entry)

        print(f"Estudo de {entry} Finalizado!")
        print('Entre com outro objeto para continuar, ou "Enter" para voltar')
        entry = filtro(input().upper())


# TODO:
def estudo_transferencia_automatica():
    """
    Gerenciador de esutdos RL TA
    """
    print('Estudo Ganho RL TA:')

    return


def selecionar_estudo():
    global CELESC
    message = "1 - Atualizar Rede\t2 - Estudo Ganho RLs NF.\t3 - Estudo Ganho RLs TA.\tx - Sair"
    print(message)
    estudo = input().upper()
    while True:
        if estudo not in ["1", "2", "3", "X"]:
            print("Entre com 1, 2, 3, ou X")
            estudo = input("-> ").upper()

        if estudo == "1":
            importar_arquivos()
            print("Arquivos importados com sucesso!")
            print("Atualizando Rede.", end='\r', flush=True)
            CELESC = CriarRede()
            print("Rede Atualizada.")
            print(
                f'Periodo do relatório 1025: {OCORRENCIAS["DATA INICIO"].min() + " - " + OCORRENCIAS["DATA FIM"].max()}')
            print("Selecione a função:")
            print(message)
            estudo = input().upper()

        if estudo == "2":
            if CELESC is None:
                print("Criando Rede:")
                CELESC = CriarRede()
                print("Rede criada!")
            estudo_ganho_rls_nf()
            print(message)
            estudo = input().upper()

        if estudo == "3":
            if CELESC is None:
                print("Criando Rede:")
                CELESC = CriarRede()
                print("Rede criada!")
            estudo_transferencia_automatica()
            print(message)
            estudo = input().upper()

        if estudo == "X":
            exit()

def mainloop():

    print('Ferramenta de Redução de DEC estimado.')
    print(f'Periodo do relatório 1025: {OCORRENCIAS["DATA INICIO"].min() + " - " + OCORRENCIAS["DATA FIM"].max()}')
    print("Selecione a função:")
    while True:
        selecionar_estudo()


if __name__ == "__main__":
    mainloop()
