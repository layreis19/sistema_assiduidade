import tkinter as tk 
from ligacao import conn
import cores
import pandas as pd

from datetime import datetime

class PaginaDashboard(tk.Frame):

    def __init__(self, parent):
        super().__init__(parent, bg=cores.BOTAO_DARK)


        self.pagina_dashboard = tk.Frame(self, background=cores.CARD)


        consulta = """
            SELECT 
                f.nome,
                r.id_funcionario,
                r.data,
                r.atraso_minutos,
                r.horas_extra_minutos,
                r.total_minutos_trabalhados
            FROM RESULTADOS as r
            INNER JOIN FUNCIONARIOS AS f
                ON r.id_funcionario = f.id_funcionario;
                
        """

        df = pd.read_sql(consulta,conn)

        # print(df.info())

        # CONVERTER DATA PARA DATETIME 
        df["data"] = pd.to_datetime(df["data"])
        # print(df.info())


        # FILTRAR OS REGISTOS DO ANO SELECIONADO 
        ano_selecionado = datetime.now().year

        df_ano = df[df["data"].dt.year == ano_selecionado]

        media_atrasos = df_ano["atraso_minutos"].mean()

        print(media_atrasos.__round__(2))


        df_atrasos = df[df["data"].dt.year == ano_selecionado]

        total_atraso_ano = df_atrasos["total_minutos_trabalhados"].mean()
       
        print(total_atraso_ano.__round__(2))


