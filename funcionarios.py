import tkinter as tk


class PaginaFuncionarios(tk.Frame):

    def __init__(self, parent):

        super().__init__(parent)

        titulo = tk.Label(
            self,
            text="GESTÃO DE FUNCIONÁRIOS",
            font=("Arial", 24)
        )

        titulo.pack(pady=50)