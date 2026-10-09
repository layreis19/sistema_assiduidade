
"""
O QUE ESTE FICHEIRO FAZ?
Página do administrador para corrigir picagens.
- Adicionar uma picagem manual (para quem se esqueceu de picar).
- Alterar uma picagem errada.
- Eliminar uma picagem errada.
 
Nada é apagado da base de dados (tabela PICAGEM):
- Eliminar  -> a picagem fica marcada como anulada (anulada = 1).
- Alterar   -> a original fica anulada e é criada uma picagem nova,
               ligada à original por picagem_original_id.
- Adicionar -> nova picagem, com o admin e o motivo registados.
Em todos os casos o motivo é obrigatório, e os resultados do dia
(atrasos, horas extra, total trabalhado) são recalculados.
"""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime, timedelta
import widgets as w
import mysql.connector
import cores
from ligacao import conn
from rotulos import rotulo_tipo_picagem
from ttkbootstrap.widgets import DateEntry
 
# Tipos de picagem usados pelo relogio_ponto.py
TIPOS = ["ENTRADA", "SAIDA_ALMOCO", "VOLTA_ALMOCO", "SAIDA"]

FORMATO_DATA = "%d/%m/%Y"
FORMATO_HORA = "%H:%M"
 
 
class PaginaPicagensAdmin(tk.Frame):
 
    def __init__(self, parent, obter_id_admin=None):
        super().__init__(parent, bg=cores.CARD)
 
        self.cursor = conn.cursor(buffered=True)
 
        # função que devolve o id do admin com sessão iniciada (ou None)
        self.obter_id_admin = obter_id_admin or (lambda: None)
 
        self.funcionarios_map = {}   # "Nome (#id)" -> id_funcionario
        self.picagens = {}           # id_picagem -> dados da linha
        self.rotulo_para_tipo = {rotulo_tipo_picagem(t): t for t in TIPOS}
 
        w.criar_titulo(self, "PICAGENS").pack(pady=(30,20))
        acoes= tk.Frame(self)
        acoes.pack(pady=10)
        
        w.criar_botao(acoes,"Adicionar picagem",self.adicionar_picagem).pack(side="left")
        w.criar_botao(acoes,"Alterar",self.alterar_picagem).pack(side="left",padx=5)
        w.criar_botao(acoes,"Eliminar",self.eliminar_picagem).pack(side="left",padx=5)
        
     
        w.criar_estilo_tabela()
 
        self.tabela = ttk.Treeview(
            self,
            columns=("funcionario", "data", "tipo", "estado", "motivo"),
            show="headings",
            selectmode="browse",
            style="Estilo_tabela"
        )
        self.tabela.heading("funcionario", text="Funcionário")
        self.tabela.heading("data", text="Data e hora")
        self.tabela.heading("tipo", text="Tipo")
        self.tabela.heading("estado", text="Estado")
        self.tabela.heading("motivo", text="Motivo da correção")
 
        self.tabela.tag_configure("anulada", foreground="#9aa5b1")
 
        self.tabela.pack(fill="both", expand=True, padx=30, pady=20)
 
        # reaplica o estilo sempre que a página aparece
        self.bind("<Map>", w.criar_estilo_tabela())
 
        self.carregar_funcionarios()
        self.atualizar_tabela()
 
    
    
 
   
    # CARREGAR A LISTA DE FUNCIONÁRIOS (usada nos formulários)
   
    def carregar_funcionarios(self):
        self.cursor.execute(
            "SELECT id_funcionario, nome, estado FROM funcionarios ORDER BY nome"
        )
        self.funcionarios_map = {}
        for id_, nome, estado in self.cursor.fetchall():
            sufixo = "" if estado == "ATIVO" else " - inativo"
            self.funcionarios_map[f"{nome} (#{id_}){sufixo}"] = id_
 
   
    # LER AS PICAGENS DA BASE DE DADOS E MOSTRAR NA TABELA
    
    def atualizar_tabela(self):
        for linha in self.tabela.get_children():
            self.tabela.delete(linha)
        self.picagens = {}
 
        try:
            self.cursor.execute(
                """
                SELECT p.id_picagem, p.id_funcionario, f.nome, p.data, p.tipo,
                       p.anulada, p.motivo_retificacao
                FROM picagem p
                JOIN funcionarios f ON f.id_funcionario = p.id_funcionario
                ORDER BY p.data DESC
                """
            )
            resultados = self.cursor.fetchall()
        except mysql.connector.Error as erro:
            messagebox.showerror("Erro", f"Erro ao consultar picagens: {erro}")
            return
 
        for id_p, id_f, nome, data, tipo, anulada, motivo in resultados:
            self.picagens[id_p] = {
                "id": id_p,
                "id_funcionario": id_f,
                "nome": nome,
                "data": data,
                "tipo": tipo,
                "anulada": bool(anulada),
            }
            self.tabela.insert(
                "", "end", iid=str(id_p),
                values=(
                    nome,
                    data.strftime("%d/%m/%Y %H:%M"),
                    rotulo_tipo_picagem(tipo),
                    "Anulada" if anulada else "Válida",
                    motivo or ""
                ),
                tags=("anulada",) if anulada else ()
            )
 
  
    # DEVOLVE A PICAGEM SELECIONADA NA TABELA (ou None)
  
    def obter_selecionada(self):
        sel = self.tabela.selection()
        if not sel:
            messagebox.showerror("Erro", "Selecione uma picagem na tabela!")
            return None
        return self.picagens.get(int(sel[0]))
 

    # RECALCULAR OS RESULTADOS (atrasos/horas extra) DO DIA AFETADO
    
    def recalcular(self, id_funcionario, data_hora, tipo):
        dias = {data_hora.date()}
        # se não for ENTRADA, pode pertencer a um turno começado na véspera
        if tipo != "ENTRADA":
            dias.add(data_hora.date() - timedelta(days=1))
 
        for dia in dias:
            try:
                calcular_e_guardar_dia(self.cursor, conn, id_funcionario, dia)
            except Exception as erro:
                print(erro)
 
    
    # 1. ADICIONAR PICAGEM MANUAL
   
    def adicionar_picagem(self):
 
        janela = tk.Toplevel(self)
        janela.title("Adicionar picagem manual")
        janela.grab_set()
 
        w.criar_label( janela,"Funcionário:").pack(pady=(10,2), padx=20)
        combo_func = ttk.Combobox(janela, values=list(self.funcionarios_map.keys()), state="readonly",width=28)
        combo_func.pack(padx=20)
        
        w.criar_label(janela, "Data (DD/MM/AAAA):").pack(pady=(10, 2), padx=20)
        entry_data = DateEntry(janela,dateformat="%d/%m/%Y",width=12, bootstyle=cores.PRIMARY_DARK)
        entry_data.pack(padx=20)
 
        w.criar_label(janela, "Hora (HH:MM):").pack(pady=(10, 2), padx=20)
        entry_hora = w.criar_entrada(janela, largura=14)
        entry_hora.pack(padx=20)
 
        w.criar_label(janela, "Tipo:").pack(pady=(10, 2), padx=20)
        combo_tipo = ttk.Combobox(
            janela, values=list(self.rotulo_para_tipo.keys()),
            state="readonly", width=20
        )
        combo_tipo.pack(padx=20)
 
        w.criar_label(janela, "Motivo (obrigatório):").pack(pady=(10, 2), padx=20)
        entry_motivo = w.criar_entrada(janela, largura=32)
        entry_motivo.pack(padx=20)
 
        def guardar():
            id_funcionario = self.funcionarios_map.get(combo_func.get())
            if id_funcionario is None:
                messagebox.showerror("Erro", "Selecione um funcionário.", parent=janela)
                return
 
            try:
                data_hora = datetime.strptime(
                    f"{entry_data.entry.get().strip()} {entry_hora.get().strip()}",
                    f"{FORMATO_DATA} {FORMATO_HORA}"
                )
            except ValueError:
                messagebox.showerror(
                    "Erro", "Data ou hora inválida.\nUse DD/MM/AAAA e HH:MM.", parent=janela
                )
                return
 
            if data_hora > datetime.now():
                messagebox.showerror("Erro", "Não é possível registar uma picagem no futuro.", parent=janela)
                return
 
            tipo = self.rotulo_para_tipo.get(combo_tipo.get())
            if tipo is None:
                messagebox.showerror("Erro", "Selecione o tipo de picagem.", parent=janela)
                return
 
            motivo = entry_motivo.get().strip()
            if not motivo:
                messagebox.showerror("Erro", "O motivo é obrigatório.", parent=janela)
                return
 
            try:
                self.cursor.execute(
                    """
                    INSERT INTO picagem
                    (id_funcionario, data, tipo, id_admin_retificacao, motivo_retificacao)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (id_funcionario, data_hora, tipo, self.obter_id_admin(), motivo)
                )
                conn.commit()
            except mysql.connector.Error as erro:
                conn.rollback()
                messagebox.showerror("Erro", f"Erro ao registar picagem:\n{erro}", parent=janela)
                return
 
            self.recalcular(id_funcionario, data_hora, tipo)
            self.atualizar_tabela()
            messagebox.showinfo("Sucesso", "Picagem registada com sucesso!")
            janela.destroy()
 
        w.criar_botao(janela,"Guardar",guardar).pack(pady=15)
 
    
    # 2. ALTERAR PICAGEM
    
    def alterar_picagem(self):
 
        picagem = self.obter_selecionada()
        if not picagem:
            return
 
        if picagem["anulada"]:
            messagebox.showerror("Erro", "Esta picagem já está anulada e não pode ser alterada.")
            return
 
        janela = tk.Toplevel(self)
        janela.title("Alterar picagem")
        janela.grab_set()
 
        tk.Label(janela, text=f"Funcionário: {picagem['nome']}").pack(pady=(10, 2), padx=20)
 
        w.criar_label(janela, "Data (DD/MM/AAAA):").pack(pady=(10, 2), padx=20)
        entry_data =DateEntry(janela, dateformat="%d/%m/%Y", startdate=picagem["data"],width=12, bootstyle=cores.PRIMARY_DARK)
        entry_data.pack(padx=20)
 
        w.criar_label(janela, "Hora (HH:MM):").pack(pady=(10, 2), padx=20)
        entry_hora = w.criar_entrada(janela, largura=14)
        entry_hora.insert(0, picagem["data"].strftime(FORMATO_HORA))
        entry_hora.pack(padx=20)
 
        w.criar_label(janela,"Tipo:").pack(pady=(10, 2), padx=20)
        combo_tipo = ttk.Combobox(
            janela, values=list(self.rotulo_para_tipo.keys()),
            state="readonly", width=20
        )
        combo_tipo.set(rotulo_tipo_picagem(picagem["tipo"]))
        combo_tipo.pack(padx=20)
 
        w.criar_label(janela,"Motivo da correção (obrigatório):").pack(pady=(10, 2), padx=20)
        entry_motivo = w.criar_entrada(janela, largura=32)
        entry_motivo.pack(padx=20)
 
        def guardar():
            try:
                nova_data = datetime.strptime(
                    f"{entry_data.entry.get().strip()} {entry_hora.get().strip()}",
                    f"{FORMATO_DATA} {FORMATO_HORA}"
                )
            except ValueError:
                messagebox.showerror(
                    "Erro", "Data ou hora inválida.\nUse DD/MM/AAAA e HH:MM.", parent=janela
                )
                return
 
            if nova_data > datetime.now():
                messagebox.showerror("Erro", "Não é possível registar uma picagem no futuro.", parent=janela)
                return
 
            novo_tipo = self.rotulo_para_tipo.get(combo_tipo.get())
            if novo_tipo is None:
                messagebox.showerror("Erro", "Selecione o tipo de picagem.", parent=janela)
                return
 
            motivo = entry_motivo.get().strip()
            if not motivo:
                messagebox.showerror("Erro", "O motivo é obrigatório.", parent=janela)
                return
 
            id_admin = self.obter_id_admin()
 
            try:
                # 1) anular a picagem original
                self.cursor.execute(
                    """
                    UPDATE picagem
                    SET anulada = 1, id_admin_retificacao = %s, motivo_retificacao = %s
                    WHERE id_picagem = %s AND anulada = 0
                    """,
                    (id_admin, motivo, picagem["id"])
                )
                if self.cursor.rowcount == 0:
                    conn.rollback()
                    messagebox.showerror(
                        "Erro", "Esta picagem já foi anulada por outra pessoa.", parent=janela
                    )
                    self.atualizar_tabela()
                    return
 
                # 2) criar a picagem corrigida, ligada à original
                self.cursor.execute(
                    """
                    INSERT INTO picagem
                    (id_funcionario, data, tipo, picagem_original_id,
                     id_admin_retificacao, motivo_retificacao)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (picagem["id_funcionario"], nova_data, novo_tipo,
                     picagem["id"], id_admin, motivo)
                )
                conn.commit()
            except mysql.connector.Error as erro:
                conn.rollback()
                messagebox.showerror("Erro", f"Erro ao alterar picagem:\n{erro}", parent=janela)
                return
 
            # recalcular o dia antigo e o novo (podem ser diferentes)
            self.recalcular(picagem["id_funcionario"], picagem["data"], picagem["tipo"])
            self.recalcular(picagem["id_funcionario"], nova_data, novo_tipo)
 
            self.atualizar_tabela()
            messagebox.showinfo("Sucesso", "Picagem alterada com sucesso!")
            janela.destroy()
 
        w.criar_botao(janela, "Guardar", guardar).pack(pady=15)
 
    
    # 3. ELIMINAR PICAGEM (anular)
   
    def eliminar_picagem(self):
 
        picagem = self.obter_selecionada()
        if not picagem:
            return
        
        motivo = simpledialog.askstring("Eliminar picagem", "Motivo (obrigatório):", parent=self)
        if not motivo or not motivo.strip():
            messagebox.showerror("Erro", "O motivo é obrigatório.")
            return
        
        self.cursor.execute(
            """
            UPDATE picagem
            SET anulada = 1, id_admin_retificacao = %s, motivo_retificacao = %s
            WHERE id_picagem = %s
            """,
            (self.obter_id_admin(), motivo.strip(), picagem["id"])
            )
        conn.commit()
        self.recalcular(picagem["id_funcionario"], picagem["data"], picagem["tipo"])
        self.atualizar_tabela()
    