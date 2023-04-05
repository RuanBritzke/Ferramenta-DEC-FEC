**Não sei um bom nome para o código**
=====================================

Glossário
----------
- **DIC** - Duração de Interrupção Individual por Unidade Consumidora ou por Ponto de Conexão: intervalo de tempo que, no período de apuração, em cada unidade consumidora ou ponto de conexão ocorreu descontinuidade da distribuição de energia elétrica.
- **DEC** - Duração Equivalente de Interrupção por Unidade Consumidora: intervalo de tempo que, em média, no período de apuração, em cada unidade consumidora do conjunto considerado ocorreu descontinuidade da distribuição de energia elétrica.
- **FIC** - Frequência de Interrupção Individual por Unidade Consumidora ou Ponto de Conexão: número de interrupções ocorridas, no período de apuração, em cada unidade consumidora ou ponto de conexão.
- **FEC** - Frequência Equivalente de Interrupção por Unidade Consumidora: número de interrupções ocorridas, em média, no período de apuração, em cada unidade consumidora do conjunto considerado. 
- **CHI** - Consumidor Hora Interrompido: somatório dos valores de Duração de Interrupção Individual por Unidade Consumidora ou Ponto de Conexão – DIC dos consumidores atingidos por interrupção no fornecimento de energia, expresso em horas e centésimos de horas. 
- **CHI Acumulado**: Somatório dos valores de CHI a jusante do ponto de referência e a jusante do ponto de referência.


Objetivos e funcionalidades que este algoritmo devem desempenhar:
---------------------------------------------------------

- Importar, tratar e salvar as informações dos relatórios extraidos do Interplan (Relatório Hierarquico de Chaves, Relatório de Chaves) e relatórios simo 1025.
- Calcular o valor do CHI das chaves do sistema a partir das informações a cima.
- Calcular o valor do CHI acumulado a jusante das chaves 
- Calcular a estimativa de redução do CHI acumulado dada a troca de uma chave por religadora.
- Calcular a estimativa de redução do CHI acumulado dada a inserção da chave em um grupo de transferencia de carga automático. \


Projeto em contrução :construction:\

Funcionalidades Futuras:
------------------------

- Estudo geral
    - redução dec ta
    - redução dec nf

- Estudo especifico (Chave, Alimentador, SE)
    Chave:\
    - Mostrar Ganho NF
    - Selecionar TA (Ida e volta, somente Ida)
    - Mostrar Ganho TA (Se FU mais a jusante ou CD)




