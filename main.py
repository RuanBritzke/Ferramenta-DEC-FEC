# ---------------------------------------
# Autor:    Ruan Carlo Weiers Britzke
# Lotação:  DPEP/DVPE
# Data:     30/03/2023
# ---------------------------------------
import os
import pandas as pd
from src._database import importar_arquivos, OCORRENCIAS
from src._dataclasses import CriarRede, Empresa, Nucleo, Subestacao, Alimentador, Chave


decimal = lambda n: float("{:.2f}".format(n))

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
            print(
                f'Nenhum objeto "{entry}" encontrado na rede.\nTente novamente ou "Enter" para encerrar:'
            )
            entry = input().upper()
            continue
        return busca


def continuar():
    print(
        '\nPara continuar entre o próximo valor. Para encerrar o estudo pressione "ENTER".'
    )
    entry = input().upper()
    return entry


def por_chave(chave: Chave):
    dic_jusante = chave.dic_jusante()
    dic_jusante_pos_rl = chave.dic_jusante_pos_rl()

    reducao_dic_jusante = dic_jusante - dic_jusante_pos_rl
    reducao_dic_jusante_p = reducao_dic_jusante / dic_jusante if dic_jusante else 0
    dic_montante = chave.dic_montante()
    dic_montante_pos_ta = chave.dic_montante_pos_ta()
    reducao_dic_montante = dic_montante - dic_montante_pos_ta
    reducao_dic_montante_p = (
        reducao_dic_montante / dic_montante if dic_montante != 0 else 0
    )

    chaves_nf = pd.DataFrame(
        {
            "Núcleo / Unidade": str(chave.nucleo),
            "SE": str(chave.subestacao),
            "Alimentador": str(chave.alimentador),
            "Chave": chave,
            "Tipo": chave.tipo,
            "UCs": chave.ucs,
            "CHI Chave [h*ucs]": decimal(chave.dic),
            "CHI estimado após substituição [h * ucs]": decimal(chave.dic_pos_rl),
            "CHI Jusante Acumulado [h * ucs]": decimal(dic_jusante),
            "CHI Jusante Acumulado estimado após substituição [h * ucs]": decimal(
                dic_jusante_pos_rl
            ),
            "Redução CHI Jusante Acumulado estimada [%]": decimal(
                100 * reducao_dic_jusante_p
            ),
            "CHI Montante Acumulado [h * ucs]": decimal(dic_montante),
            "CHI Montante Acumulado estimado após TA [h * ucs]": decimal(
                dic_montante_pos_ta
            ),
            "Redução CHI Montante Acumulado estimado [%]": decimal(
                100 * reducao_dic_montante_p
            ),
            "Redução Total [h * ucs]": decimal(
                reducao_dic_jusante + reducao_dic_montante
            ),
        },
        index=["0"],
    )

    print(
        chaves_nf.tail(1)
        .transpose()
        .to_string(columns=chaves_nf.columns.to_list().remove("Chave"), header=None)
    )
    with pd.ExcelWriter(
        "Estudo.xlsx", engine="openpyxl", mode="a", if_sheet_exists="overlay"
    ) as writer:
        chaves_nf.to_excel(
            writer,
            index=False,
            sheet_name="Estudo por Chave",
            startrow=writer.sheets["Estudo por Chave"].max_row,
            header=None,
        )
    return


def por_alimentador(alm: Alimentador):
    print("Calculando valores, isso pode levar alguns segundos", end="\r")
    df = pd.DataFrame(alm.chaves_candidatas(), columns=["Chave"])
    ucs = alm.ucs
    df["Tipo"] = df["Chave"].apply(lambda x: x.tipo)
    df["Redução CHI a jusante estimada"] = df["Chave"].apply(
        lambda x: decimal((x.dic_jusante() - x.dic_jusante_pos_rl()))
    )
    df["Redução CHI a montante estimada"] = df["Chave"].apply(
        lambda x: decimal(x.dic_montante() - x.dic_montante_pos_ta())
    )
    df["Redução CHI total estimada"] = (
        df["Redução CHI a jusante estimada"] + df["Redução CHI a montante estimada"]
    )
    df["Interrupções chave"] = df["Chave"].apply(lambda x: x.qtd_ocorrencias)
    df["Interrupções a jusante"] = df["Chave"].apply(
        lambda x: len(x.ocorrencias_jusante)
    )
    df["Unidades consumidoras a jusante da Chave"] = df["Chave"].apply(lambda x: x.ucs)
    df["Unidades consumidoras do Alimentador"] = ucs
    df = df[(df["Redução CHI total estimada"]) != 0]
    if df.empty:
        print("Nenhuma chave encontrada para substituição!       ")
    print(f"Unidades Consumidoras {alm}: {ucs}                   ")
    df.sort_values("Redução CHI total estimada", inplace=True, ascending=False)
    print(df.head(10).to_string(index=False)) if not df.empty else None
    if alm.SED:
        print(f"Atenção SED {alm.SED} no Alimentador!")
    if not os.path.exists("Estudo.xlsx"):
        pd.DataFrame().to_excel("Estudo.xlsx", index=False)
    with pd.ExcelWriter(
        "Estudo.xlsx", engine="openpyxl", mode="a", if_sheet_exists="replace"
    ) as writer:
        df.to_excel(writer, index=False, sheet_name=f"Estudo Aliementador {str(alm)}")
    return


def por_subestacao(se: Subestacao):
    print("Calculando. Este processo pode levar alguns minutos.", end="\r")
    df = pd.DataFrame(se.chaves_candidatas(), columns=["Chave"])
    ucs = se.ucs

    df["Alimentador"] = df["Chave"].apply(lambda x: x.alimentador)
    df = df[["Alimentador", "Chave"]]
    df["Tipo"] = df["Chave"].apply(lambda x: x.tipo)
    df["Redução CHI estimada a jusante"] = df.apply(
        lambda x: decimal(x["Chave"].dic_jusante() - x["Chave"].dic_jusante_pos_rl()),
        axis=1,
    )
    df["Redução CHI estimada a montante"] = df.apply(
        lambda x: decimal(x["Chave"].dic_montante() - x["Chave"].dic_montante_pos_ta()),
        axis=1,
    )
    df["Redução CHI total estimada"] = df.apply(
        lambda x: x["Redução CHI estimada a jusante"]
        + x["Redução CHI estimada a montante"],
        axis=1,
    )
    df["Interrupções"] = df["Chave"].apply(lambda x: x.qtd_ocorrencias)
    df["UCs a jusante da Chave"] = df["Chave"].apply(lambda x: x.ucs)
    df = df[df["Redução CHI total estimada"] != 0]
    if df.empty:
        print("Nenhuma chave encontrada para substituição!")
    df.sort_values(["Redução CHI total estimada"], inplace=True, ascending=False)
    print(f"Unidades Consumidoras {se}: {ucs}                    ")
    print(df.head(10).to_string(index=False)) if not df.empty else None

    with pd.ExcelWriter(
        "Estudo.xlsx", engine="openpyxl", mode="a", if_sheet_exists="replace"
    ) as writer:
        df.to_excel(writer, index=False, sheet_name=f"Estudo Subestação {str(se)}")
    return


def por_nucleo(nu: Nucleo):
    print("Calculando. Este processo pode levar alguns minutos.", end="\r")
    df = pd.DataFrame(nu.chaves_candidatas(), columns=["Chave"])
    ucs = nu.ucs
    df["Substação"] = df["Chave"].apply(lambda x: x.subestacao)
    df["Alimentador"] = df["Chave"].apply(lambda x: x.alimentador)
    df = df[["Subestação", "Alimentador", "Chave"]]
    df["Tipo"] = df["Chave"].apply(lambda x: x.tipo)
    df["Redução DEC estimada a jusante  [HI]"] = df.apply(
        lambda x: (x["Chave"].dic_jusante() - x["Chave"].dic_jusante_pos_rl()) / ucs,
        axis=1,
    )
    df["Redução DEC estimada a montante [HI]"] = df.apply(
        lambda x: (x["Chave"].dic_montante() - x["Chave"].dic_montante_pos_ta()) / ucs,
        axis=1,
    )
    df["Redução DEC total estimada [HI]"] = df.apply(
        lambda x: x["Redução DEC estimada a jusante  [HI]"]
        + x["Redução DEC estimada a montante [HI]"],
        axis=1,
    )
    df["Interrupções"] = df["Chave"].apply(lambda x: x.qtd_ocorrencias)
    df["UCs a jusante da Chave"] = df["Chave"].apply(lambda x: x.ucs)
    df = df[df["Redução DEC total estimada [HI]"] != 0]
    if df.empty:
        print("Nenhuma chave encontrada para o núcleo!")
    df.sort_values(["Redução DEC total estimada [HI]"], inplace=True, ascending=False)
    print(f"Unidades Consumidoras {nu}: {ucs}                    ")
    print(df.head(20).to_string(index=False)) if not df.empty else None
    with pd.ExcelWriter(
        "Estudo.xlsx", engine="openpyxl", mode="a", if_sheet_exists="replace"
    ) as writer:
        df.to_excel(writer, index=False, sheet_name=f"Estudo Núcleo {str(nu)}")
    return


def empresa():
    print("Calculando. Este processo pode levar alguns minutos.", end="\r")
    df = pd.DataFrame(CELESC.chaves_candidatas(), columns=["Chave"])
    ucs = CELESC.ucs
    df["Núcleo"] = df["Chave"].apply(lambda x: x.nucleo)
    df["Subestação"] = df["Chave"].apply(lambda x: x.subestacao)
    df["Alimentador"] = df["Chave"].apply(lambda x: x.alimentador)
    df = df[["Núcleo", "Subestação", "Alimentador", "Chave"]]
    df["Tipo"] = df["Chave"].apply(lambda x: x.tipo)
    df["Redução DEC estimada a jusante  [HI]"] = df.apply(
        lambda x: (x["Chave"].dic_jusante() - x["Chave"].dic_jusante_pos_rl()) / ucs,
        axis=1,
    )
    df["Redução DEC estimada a montante [HI]"] = df.apply(
        lambda x: (x["Chave"].dic_montante() - x["Chave"].dic_montante_pos_ta()) / ucs,
        axis=1,
    )
    df["Redução DEC total estimada [HI]"] = df.apply(
        lambda x: x["Redução DEC estimada a jusante  [HI]"]
        + x["Redução DEC estimada a montante [HI]"],
        axis=1,
    )
    df["Interrupções"] = df["Chave"].apply(lambda x: x.qtd_ocorrencias)
    df["UCs a jusante da Chave"] = df["Chave"].apply(lambda x: x.ucs)
    df = df[df["Redução DEC total estimada [HI]"] != 0]
    if df.empty:
        print("Nenhuma chave encontrada para o núcleo!")
    df.sort_values(["Redução DEC total estimada [HI]"], inplace=True, ascending=False)
    print(f"Unidades Consumidoras {CELESC}: {ucs}                    ")
    print(df.to_string(index=False)) if not df.empty else None
    with pd.ExcelWriter(
        "Estudo.xlsx", engine="openpyxl", mode="a", if_sheet_exists="replace"
    ) as writer:
        df.to_excel(writer, index=False, sheet_name=f"Estudo CELESC")
    return


def esudo_geral():
    """
    Gerenciador de estudos gerais.
    """
    print("Estudo geral visa encontrar candidatas para substituição por religadora.")
    print(
        "A redução do CHI a montante é calculada para cada chave usando TA dentro da mesma SE."
    )
    print(
        'Entre com uma Chave, Alimentador, ou SE para começar a análise.\nPara voltar pressione "Enter"'
    )
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

        if entry.__class__.__name__ == "Nucleo":
            por_nucleo(entry)

        if entry.__class__.__name__ == "Empresa":
            empresa()

        print(f"Estudo de {entry} Finalizado!")
        print('Entre com outro objeto para continuar, ou "Enter" para voltar')
        entry = filtro(input().upper())


def selecionar_funcao():
    global CELESC
    message = "1 - Atualizar Rede\t2 - Estudo.\tx - Sair"
    print(message)
    estudo = input().upper()
    while True:
        if estudo not in ["1", "2", "3", "X"]:
            print("Entre com 1, 2, 3, ou X")
            estudo = input().upper()

        if estudo == "1":
            importar_arquivos()
            print("Arquivos importados com sucesso!")
            print("Atualizando Rede.", end="\r", flush=True)
            CELESC = CriarRede()
            print("Rede Atualizada.")
            print(
                f'Periodo do relatório 1025: {OCORRENCIAS["DATA INICIO"].min() + " - " + OCORRENCIAS["DATA FIM"].max()}'
            )
            print("Selecione a função:")
            print(message)
            estudo = input().upper()

        if estudo == "2":
            if CELESC is None:
                print("Criando Rede:")
                CELESC = CriarRede()
                print("Rede criada!")
            if not os.path.exists("Estudo.xlsx"):
                pd.DataFrame(
                    columns=[
                        "Núcleo / Unidade",
                        "SE",
                        "Alimentador",
                        "Chave",
                        "Tipo",
                        "CHI Chave [h*ucs]",
                        "CHI estimado após substituição [h * ucs]",
                        "CHI Jusante Acumulado [h * ucs]",
                        "CHI Jusante Acumulado estimado após substituição [h * ucs]",
                        "Redução CHI Jusante Acumulado estimada [%]",
                        "CHI Montante Acumulado [h * ucs]",
                        "CHI Montante Acumulado estimado após TA [h * ucs]",
                        "Redução CHI Montante Acumulado estimado [%]",
                        "Redução Total [h * ucs]",
                    ]
                ).to_excel("Estudo.xlsx", index=False, sheet_name="Estudo por Chave")
            esudo_geral()
            print(message)
            estudo = input().upper()

        if estudo == "X":
            exit()


def mainloop():

    print("Ferramenta de Redução de DEC estimado.")
    print(
        f'Periodo do relatório 1025: {OCORRENCIAS["DATA INICIO"].min() + " - " + OCORRENCIAS["DATA FIM"].max()}'
    )
    print("Selecione a função:")
    while True:
        selecionar_funcao()


if __name__ == "__main__":
    mainloop()
