import os
from dotenv import load_dotenv
import mysql.connector
import tkinter as tk
from tkinter import ttk, messagebox

load_dotenv()  


conn = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME")
)

cursor = conn.cursor()

print("Ligação bem sucedida!")
