"""
O QUE ESTE FICHEIRO FAZ?
É o ficheiro principal: arranca a aplicação.
- Cria a janela e o menu com os botões.
- Cria todas as páginas e mostra uma de cada vez.
- Antes do login, o menu tem 3 botões: Relógio de Ponto, Presenças e Administrador.
- Depois do login, aparecem também Funcionários, Horários, Relatórios e Sair.
- O botão Sair volta ao menu inicial de 3 botões.
Para usar a aplicação, corre este ficheiro.
"""

import tkinter as tk
from relogio_ponto import PaginaPonto
from funcionarios import PaginaFuncionarios
from ctrl_presencas import PaginaPresencas
from administrador import PaginaAdministrador
from relatorios import PaginaRelatorios
from atribuicao_horario import PaginaAtribuicaoHorarios
from ligacao import conn

janela = tk.Tk()
janela.title("Gestão de Assiduidade")
janela.geometry("900x600")


# MENU
menu = tk.Frame(janela, bg="lightgray")
menu.pack(side="top", fill="x")

# ÁREA DAS PÁGINAS
conteudo = tk.Frame(janela)
conteudo.pack(side="top", fill="both", expand=True)


# CRIAR AS PÁGINAS 
pagina_ponto = PaginaPonto(conteudo)
pagina_funcionarios = PaginaFuncionarios(conteudo)
pagina_presencas = PaginaPresencas(conteudo)
pagina_relatorios = PaginaRelatorios(conteudo)
pagina_atribuicao_horarios = PaginaAtribuicaoHorarios(conteudo)



def mostrar_pagina(pagina):
    # esconder todas as páginas
    pagina_ponto.pack_forget()
    pagina_presencas.pack_forget()
    pagina_administrador.pack_forget()
    pagina_relatorios.pack_forget()
    pagina_atribuicao_horarios.pack_forget()
    pagina_funcionarios.pack_forget()

    # mostrar a página escolhida
    pagina.pack(fill="both", expand=True)

    # atualizar dados de algumas páginas
    if pagina == pagina_ponto:
        pagina_ponto.carregar_funcionarios()

    elif pagina == pagina_presencas:
        pagina_presencas.atualizar_presenca()

    elif pagina == pagina_atribuicao_horarios:
        pagina_atribuicao_horarios.carregar_funcionarios()
        pagina_atribuicao_horarios.carregar_horarios()


def mostrar_botoes_admin():
    # chamada quando o login corre bem
    btn_administrador.pack_forget()

    btn_funcionarios.pack(side="left", padx=10, pady=10)
    btn_horarios.pack(side="left", padx=10, pady=10)
    btn_relatorios.pack(side="left", padx=10, pady=10)
    btn_sair.pack(side="left", padx=10, pady=10)

    mostrar_pagina(pagina_funcionarios)


def sair_admin():
    # esconder os botões de admin
    btn_funcionarios.pack_forget()
    btn_horarios.pack_forget()
    btn_relatorios.pack_forget()
    btn_sair.pack_forget()

    # voltar a mostrar o botão Administrador
    btn_administrador.pack(side="left", padx=10, pady=10)

    # preparar o login para a próxima vez
    pagina_administrador.reiniciar_login()

    # voltar à página inicial
    mostrar_pagina(pagina_ponto)


#MENU
btn_ponto = tk.Button(
    menu,
    text="Relógio de Ponto",
    command=lambda: mostrar_pagina(pagina_ponto))
btn_ponto.pack(side="left", padx=10, pady=10)

btn_presencas = tk.Button(
    menu,
    text="Presenças",
 command=lambda: mostrar_pagina(pagina_presencas))
btn_presencas.pack(side="left", padx=10, pady=10)

btn_administrador = tk.Button(
    menu, 
    text="Administrador",
     command=lambda: mostrar_pagina(pagina_administrador))
btn_administrador.pack(side="left", padx=10, pady=10)

# botões de admin (só aparecem depois do login)
btn_funcionarios = tk.Button(
    menu,
    text="Funcionários",
  command=lambda: mostrar_pagina(pagina_funcionarios))

btn_horarios = tk.Button(
    menu,
    text="Horários",
    command=lambda: mostrar_pagina(pagina_atribuicao_horarios))

btn_relatorios = tk.Button(
    menu,
    text="Relatórios",
    command=lambda: mostrar_pagina(pagina_relatorios))

btn_sair = tk.Button(
    menu,
    text="Sair",
    command=sair_admin)


# PÁGINA DO ADMINISTRADOR (precisa da função mostrar_botoes_admin)
pagina_administrador = PaginaAdministrador(conteudo, mostrar_botoes_admin)


# PÁGINA INICIAL
mostrar_pagina(pagina_ponto)

janela.mainloop()