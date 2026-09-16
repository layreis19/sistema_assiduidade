import tkinter as tk


class PaginaPresencas(tk.Frame):

    def __init__(self, parent):

        super().__init__(parent)

        titulo = tk.Label(
            self,
            text="CONTROLO DE PRESENÇAS",
            font=("Arial", 24)
        )

        titulo.pack(pady=50)