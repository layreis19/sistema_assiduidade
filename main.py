
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
menu = tk.Frame(
    janela,
    bg="lightgray"
)

menu.pack(
    side="top",
    fill="x"
)


# ÁREA DAS PÁGINAS

conteudo = tk.Frame(janela)

conteudo.pack(
    side="top",
    fill="both",
    expand=True
)


# CRIAR AS PÁGINAS

pagina_ponto = PaginaPonto(conteudo)
pagina_funcionarios = PaginaFuncionarios(conteudo)
pagina_presencas = PaginaPresencas(conteudo)
pagina_administrador = PaginaAdministrador(conteudo)
pagina_relatorios = PaginaRelatorios(conteudo)
pagina_atribuicao_horarios = PaginaAtribuicaoHorarios(conteudo)

#mostrar a página inicial (página de ponto) e esconder as outras páginas
def mostrar_pagina(pagina):

    pagina_ponto.pack_forget()
    pagina_presencas.pack_forget()
    pagina_administrador.pack_forget()
    pagina_relatorios.pack_forget()
    pagina_atribuicao_horarios.pack_forget()

  # mostrar a página selecionada
    pagina.pack(
        fill="both",
        expand=True
    )


    # Se a página atual for a página de ponto, carregar os funcionários no combobox
    if pagina == pagina_ponto:
        pagina_ponto.carregar_funcionarios()

    elif pagina == pagina_presencas:
        pagina_presencas.atualizar_presenca()
    
    elif pagina == pagina_atribuicao_horarios:
        # Recarregar para apanhar funcionários/horários criados entretanto
        pagina_atribuicao_horarios.carregar_funcionarios()
        pagina_atribuicao_horarios.carregar_horarios()
   

  
        





# BOTÕES DO MENU

tk.Button(
    menu,
    text="Relógio de Ponto",
    command=lambda: mostrar_pagina(pagina_ponto)
).pack(side="left", padx=10, pady=10)



tk.Button(
    menu,
    text="Presenças",
    command=lambda: mostrar_pagina(pagina_presencas)
).pack(side="left", padx=10, pady=10)

tk.Button(
    menu,
    text="Administrador",
    command=lambda:  mostrar_pagina(pagina_administrador)
).pack(side="left", padx=10, pady=10)

tk.Button(
    menu,
    text="Horários",
    command=lambda: mostrar_pagina(pagina_atribuicao_horarios)
).pack(side="left", padx=10, pady=10)

# PÁGINA INICIAL

mostrar_pagina(pagina_ponto)


janela.mainloop()