import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import bcrypt
import mysql.connector
from ligacao import conn 




BG = "#EAF6FF"             # Fundo principal
PRIMARY = "#3F8FC1"        # Azul principal
PRIMARY_DARK = "#2F78A8"   # Azul mais escuro
BLUE_LIGHT = "#B5D9EA"     # Azul claro
BLUE_VERY_LIGHT = "#D9EDF7"
CARD = "#FFFFFF"           # Branco
TEXT = "#1E3A52"           # Texto principal
TEXT_SECONDARY = "#6B879C" # Texto secundário
BORDER = "#C7E3F2"


class PaginaRelatorios(tk.Frame):
    def __init__(self,parent):
        super().__init__(parent, bg= BG)
        self.parent= parent
        self.cursor = conn.cursor(buffered=True)
        
        
        
        titulo = tk.Label(  self,text="RELATÓRIOS DE ASSIDUIDADE",font=("Arial", 24))
        titulo.pack(pady=50)