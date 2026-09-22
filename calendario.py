import ttkbootstrap
from datetime import datetime


def ver_data():

    # Data escolhida no calendário
    data_texto = calendario.entry.get()

    # Transformar texto em data
    data = datetime.strptime(
        data_texto,
        "%d/%m/%Y"
    )

    # Agora podes mexer individualmente na data
    dia = data.day
    mes = data.month
    ano = data.year

    print("Data:", data)
    print("Dia:", dia)
    print("Mês:", mes)
    print("Ano:", ano)

    data_label.config(
        text=f"Dia: {dia} | Mês: {mes} | Ano: {ano}"
    )


janela = ttkbootstrap.Window(
    themename="flatly"
)

janela.title("Relatório de Assiduidade")
janela.state("zoomed")


titulo = ttkbootstrap.Label(
    janela,
    text="RELATÓRIO DE ASSIDUIDADE",
    font=("Arial", 24, "bold"),
    bootstyle="info"
)

titulo.pack(pady=(40, 20))


calendario = ttkbootstrap.DateEntry(
    janela,
    date_format="%d/%m/%Y",
    width=15,
    bootstyle="info"
)

calendario.pack(pady=20)


botao = ttkbootstrap.Button(
    janela,
    text="Ver Registo",
    command=ver_data,
    width=20,
    bootstyle="info"
)

botao.pack(pady=20)


data_label = ttkbootstrap.Label(
    janela,
    text="Nenhuma data selecionada",
    font=("Arial", 14),
    bootstyle="info"
)

data_label.pack(pady=20)


janela.mainloop()