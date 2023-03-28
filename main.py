import pandas as pd
from src._database import importar_arquivos
from src._dataclasses import CriarRede, Empresa, Nucleo, Subestacao, Alimentador, Chave




def filtro_chave() -> str:
    entry = input("-> ")
    while True:
        busca = CELESC.find(entry)
        if busca == None:
            print(f'Nenhuma objeto "{entry}" encontrado na rede.')
            if continuar_estudo():
                entry = input("Digite uma chave:\n-> ")
                continue
            return False
        if not isinstance(busca, Chave):
            print("Por favor, entre com uma chave.")
            entry = input("Digite uma chave:\n-> ")
            continue
        break
    return busca


def filtro_ta() -> str:
    entry = int(input("-> "))
    while True:
        if entry not in [1, 2]:
            print(
                'Entrada invalida, digite "1" para selecionar TA na mesma SE, ou "2" para TA em SEs diferentes'
            )
            entry = int(input("-> "))
            continue
        return entry


def continuar_estudo() -> bool:
    print('\nPara continuar pressione "Enter", para encerrar digite "Voltar"')
    entry = input("").upper()
    if entry == "VOLTAR":
        return False
    return True


def estudo_ganho_rls_nf():
    chaves_nf = pd.DataFrame()
    print('Entre com a chave a pesquisar no formato "XXX_1234".')

    i = 0
    while True:

        chave: Chave = filtro_chave()
        if not chave:
            break

        dic_acumulado = chave.dic_acumulado()
        dec_acumulado = chave.dec_acumulado()
        dic_acumulado_futuro = chave.dic_acumulado_futuro()
        dec_acumulado_futuro = chave.dec_acumulado_futuro()
        reducao_dic_acumulado = (
            round(100 * (1 - dic_acumulado_futuro / dic_acumulado), 2)
            if dic_acumulado
            else "NA"
        )
        reducao_dec = (
            round(100 * (1 - dec_acumulado_futuro / dec_acumulado), 2)
            if dec_acumulado
            else "NA"
        )

        new_line = {
            "Núcleo / Unidade": str(chave.get_nucleo()),
            "Subestação": str(chave.get_subestacao()),
            "Alimentador": str(chave.get_alimentador()),
            "Chave Referência": str(chave),
            "Unidade Consumidoras": chave.ucs_jusante(),
            "DIC Chave [h*ucs]": chave.dic(),
            "DEC Chave [h]": chave.dec(),
            "DIC Acumulado [h * ucs]": dic_acumulado,
            "DEC Acumulado [h]": dec_acumulado,
            "DIC Futuro [h * ucs]": chave.dic_futuro(),
            "DEC Futuro [h]": chave.dec_futuro(),
            "DIC Acumulado Futuro [h * ucs]": dic_acumulado_futuro,
            "DEC Acumulado Futuro [h]": dec_acumulado_futuro,
            "Redução DIC Acumulado [%]": reducao_dic_acumulado,
            "Redução DEC: [%]": reducao_dec,
        }
        chaves_nf = pd.concat([chaves_nf, pd.DataFrame(new_line, index=[i])])
        i += 1
        print(chaves_nf.tail(1).transpose().to_string(header=None))
        chaves_nf.to_excel("Estudo Ganho RLs NF.xlsx", index=False)

        if continuar_estudo():
            continue
        return


def estudo_transferencia_automatica(i):
    # TODO:
    tipos = [
        "MITIGACAO TA MESMA SE",
        "MITIGACAO TA SE DIFERENTE",
    ]
    tipo = tipos[i - 1]
    return


def selecionar_estudo():
    estudo = input("1 - Estudo Ganho RLs NF.\t2 - Estudo Ganho RLs TA.\t3 - Importar Dados\tx - Sair\n-> ").upper()
    while True:
        if estudo not in ["1", "2", "3", "X"]:
            print("Entre com 1, 2, 3, ou X")
            estudo = input("-> ").upper()
            continue
        if estudo == "1":
            global CELESC
            CELESC = CriarRede()
            estudo_ganho_rls_nf()
            estudo = input("-> ").upper()
        if estudo == "2":
            print(
                "1 - Transferencia Automatica Mesma SE\n2 - Transferência Automática SE diferente"
            )
            estudo_transferencia_automatica(filtro_ta())
            estudo = input("-> ").upper()
        if estudo == "3":
            importar_arquivos()
            estudo = input("1 - Estudo Ganho RLs NF.\t2 - Estudo Ganho RLs TA.\t3 - Importar Dados\tx - Sair\n-> ").upper()
        if estudo == "X":
            exit()



def mainloop():

    # Temporariamente sem interface de usuario, buscas e resultados são mostrados no terminal
    print("Selecione a função:")
    while True:
        selecionar_estudo()


if __name__ == "__main__":
    mainloop()
