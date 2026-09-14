import mysql.connector
import tkinter as tk
from tkinter import ttk, messagebox




conn = mysql.connector.connect(
    host="127.0.0.1",
    user="root",
    password="reis2016",
    database="ASSIDUIDADE"
)

cursor = conn.cursor()

print("Ligação bem sucedida!")
