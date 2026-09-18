import tkinter as tk 
from ligacao import conn 


class PaginaAdministrador(tk.Frame):

    def __init__(self, parent):
        super().__init__(parent)

        self.cursor = conn.cursor()
        titulo = tk.Label(
            self,
            text= "ADMINISTRADOR",
            font=("Arial",24))

        titulo.pack(pady=50)
        