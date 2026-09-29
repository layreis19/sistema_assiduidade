"""
O QUE ESTE FICHEIRO FAZ?
Página do administrador para corrigir picagens.
- Adicionar uma picagem manual (para quem se esqueceu de picar).
- Alterar uma picagem errada.
- Eliminar uma picagem errada.

Nada é apagado da base de dados. Seguindo o desenho da tabela PICAGEM:
- Eliminar  -> a picagem fica marcada como anulada (anulada = 1).
- Alterar   -> a original fica anulada e é criada uma picagem nova,
               ligada à original por picagem_original_id.
- Adicionar -> nova picagem, com o admin e o motivo registados.
Em todos os casos o motivo é obrigatório e os resultados do dia
(atrasos, horas extra, total trabalhado) são recalculados.
"""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime, timedelta
from datetime import datetime
from ttkbootstrap.widgets import DateEntry
import mysql.connector
import cores
from ligacao import conn
from calculo_assiduidade import calcular_e_guardar_dia
from rotulos import rotulo_tipo_picagem

# Tipos de picagem usados pelo relogio_ponto.py
TIPOS = ["ENTRADA", "SAIDA_ALMOCO", "VOLTA_ALMOCO", "SAIDA"]

FORMATO_DATA = "%d/%m/%Y"
FORMATO_HORA = "%H:%M"


def criar_botao(parent, texto, comando):
    """Botão com as cores do cores.py."""
    return tk.Button(
        parent,
        text=texto,
        command=comando,
        bg=cores.PRIMARY,
        fg=cores.CARD,
        activebackground=cores.PRIMARY_DARK,
        activeforeground=cores.CARD,
        relief="flat",
        bd=0,
        padx=14,
        pady=6,
        font=("Arial", 11),
        cursor="hand2"
    )


class PaginaPicagensAdmin(tk.Frame):

    def __init__(self, parent, obter_id_admin=None):
        super().__init__(parent, bg=cores.CARD)

        self.cursor = conn.cursor(buffered=True)

        # função que devolve o id do admin que fez login (ou None)
        self.obter_id_admin = obter_id_admin or (lambda: None)

        self.funcionarios_map = {}   # "Nome (#id)" -> id_funcionario
        self.picagens = {}           # id_picagem -> dados da linha
        self.rotulo_para_tipo = {rotulo_tipo_picagem(t): t for t in TIPOS}

        tk.Label(
            self, text="PICAGENS", font=("Arial", 24),
            bg=cores.CARD, fg=cores.TEXT
        ).pack(pady=15)

        # ---------------- FILTROS ----------------
        filtros = tk.Frame(self, bg=cores.CARD)
        filtros.pack(pady=5)

        tk.Label(filtros, text="Funcionário:", bg=cores.CARD, fg=cores.TEXT,
                 font=("Arial", 11)).pack(side="left", padx=(0, 5))
        self.combo_filtro = ttk.Combobox(filtros, state="readonly", width=25)
        self.combo_filtro.pack(side="left", padx=(0, 15))

        
        
        tk.Label(filtros, text="Data (DD/MM/AAAA):", bg=cores.CARD, fg=cores.TEXT,
                 font=("Arial", 11)).pack(side="left", padx=(0, 5))
        self.entry_filtro_data = tk.Entry(filtros, width=12)
        self.entry_filtro_data.pack(side="left", padx=(0, 15))


        self.var_anuladas = tk.BooleanVar(value=False)
        tk.Checkbutton(
            filtros, text="Mostrar anuladas", variable=self.var_anuladas,
            command=self.atualizar_tabela, bg=cores.CARD, fg=cores.TEXT,
            activebackground=cores.CARD, selectcolor=cores.CARD
        ).pack(side="left", padx=(0, 15))

        criar_botao(filtros, "Filtrar",self.atualizar_tabela).pack(side="left", padx=5)
        criar_botao(filtros, "Limpar", self.limpar_filtros).pack(side="left", padx=5)

        # ---------------- BOTÕES DE AÇÃO ----------------
        acoes = tk.Frame(self, bg=cores.CARD)
        acoes.pack(pady=10)

        criar_botao(acoes, "Adicionar picagem", self.adicionar_picagem).pack(side="left", padx=10)
        criar_botao(acoes, "Alterar", self.alterar_picagem).pack(side="left", padx=10)
        criar_botao(acoes, "Eliminar", self.eliminar_picagem).pack(side="left", padx=10)

        # ---------------- TABELA ----------------
        self.aplicar_estilo()

        frame_tabela = tk.Frame(self, bg=cores.CARD)
        frame_tabela.pack(fill="both", expand=True, padx=30, pady=(5, 20))

        self.tabela = ttk.Treeview(
            frame_tabela,
            columns=("funcionario", "data", "tipo", "estado", "motivo"),
            show="headings",
            selectmode="browse",
            style="Pic.Treeview"
        )
        self.tabela.heading("funcionario", text="Funcionário")
        self.tabela.heading("data", text="Data e hora")
        self.tabela.heading("tipo", text="Tipo")
        self.tabela.heading("estado", text="Estado")
        self.tabela.heading("motivo", text="Motivo da correção")

        self.tabela.column("funcionario", width=180)
        self.tabela.column("data", width=140, anchor="center")
        self.tabela.column("tipo", width=130, anchor="center")
        self.tabela.column("estado", width=90, anchor="center")
        self.tabela.column("motivo", width=280)

        self.tabela.tag_configure("anulada", foreground="#9aa5b1")

        scroll = ttk.Scrollbar(frame_tabela, orient="vertical", command=self.tabela.yview)
        self.tabela.configure(yscrollcommand=scroll.set)
        self.tabela.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        # reaplica o estilo sempre que a página aparece
        self.bind("<Map>", self.aplicar_estilo)

        self.carregar_funcionarios()
        self.atualizar_tabela()

   
    # ESTILO
    def aplicar_estilo(self, event=None):
        estilo = ttk.Style()
        if estilo.theme_use() != "clam":
            estilo.theme_use("clam")
        estilo.configure(
            "Pic.Treeview",
            background=cores.CARD,
            foreground=cores.TEXT,
            fieldbackground=cores.CARD,
            rowheight=28,
            font=("Arial", 11)
        )
        estilo.configure(
            "Pic.Treeview.Heading",
            font=("Arial", 11, "bold"),
            background=cores.BLUE_VERY_LIGHT,
            foreground=cores.TEXT
        )
        estilo.map(
            "Pic.Treeview",
            background=[("selected", cores.PRIMARY)],
            foreground=[("selected", cores.CARD)]
        )

  
    # DADOS
    def carregar_funcionarios(self):
        self.cursor.execute(
            "SELECT id_funcionario, nome, estado FROM funcionarios ORDER BY nome"
        )
        self.funcionarios_map = {}
        for id_, nome, estado in self.cursor.fetchall():
            sufixo = "" if estado == "ATIVO" else " - inativo"
            self.funcionarios_map[f"{nome} (#{id_}){sufixo}"] = id_

        self.combo_filtro["values"] = ["Todos"] + list(self.funcionarios_map.keys())
        if not self.combo_filtro.get():
            self.combo_filtro.set("Todos")

    def limpar_filtros(self):
        self.combo_filtro.set("Todos")
        self.entry_filtro_data.delete(0, tk.END)
        self.var_anuladas.set(False)
        self.atualizar_tabela()


    def obter_selecionada(self):
        sel = self.tabela.selection()
        if not sel:
            messagebox.showerror("Erro", "Selecione uma picagem na tabela!")
            return None
        return self.picagens.get(int(sel[0]))

    def recalcular(self, id_funcionario, data_hora, tipo):
        """
        Recalcula os resultados do dia afetado. Se a picagem não for uma
        ENTRADA, pode pertencer a um turno que começou na véspera (turno
        da noite), por isso recalcula também o dia anterior.
        """
        dias = {data_hora.date()}
        if tipo != "ENTRADA":
            dias.add(data_hora.date() - timedelta(days=1))

        for dia in dias:
            try:
                calcular_e_guardar_dia(self.cursor, conn, id_funcionario, dia)
            except Exception as erro:
                print(erro)

   
    # FORMULÁRIO (usado por Adicionar e Alterar)
    def formulario(self, titulo, nome_fixo, data_txt, hora_txt, tipo,):
        janela = tk.Toplevel(self)
        janela.title(titulo)
        janela.configure(bg=cores.CARD)
        janela.transient(self.winfo_toplevel())
        janela.grab_set()

        def campo(texto):
            tk.Label(janela, text=texto, bg=cores.CARD, fg=cores.TEXT,
                     font=("Arial", 11)).pack(pady=(10, 2), padx=20)

        combo_func = None
        if nome_fixo is None:
            campo("Funcionário:")
            combo_func = ttk.Combobox(
                janela, values=list(self.funcionarios_map.keys()),
                state="readonly", width=28
            )
            combo_func.pack(padx=20)
        else:
            campo(f"Funcionário: {nome_fixo}")

        campo("Data (DD/MM/AAAA):")
        entry_data = tk.Entry(janela, width=14)
        entry_data.insert(0, data_txt)
        entry_data.pack(padx=20)

        campo("Hora (HH:MM):")
        entry_hora = tk.Entry(janela, width=14)
        entry_hora.insert(0, hora_txt)
        entry_hora.pack(padx=20)

        campo("Tipo:")
        combo_tipo = ttk.Combobox(
            janela, values=list(self.rotulo_para_tipo.keys()),
            state="readonly", width=20
        )
        if tipo:
            combo_tipo.set(rotulo_tipo_picagem(tipo))
        combo_tipo.pack(padx=20)

        campo("Motivo (obrigatório):")
        entry_motivo = tk.Entry(janela, width=32)
        entry_motivo.pack(padx=20)

        #atualizar tabela
    def atualizar_tabela(self):
        for linha in self.tabela.get_children():
            self.tabela.delete(linha)
        self.picagens = {}

        query = """
            SELECT p.id_picagem, p.id_funcionario, f.nome, p.data, p.tipo,
                   p.anulada, p.motivo_retificacao
            FROM picagem p
            JOIN funcionarios f ON f.id_funcionario = p.id_funcionario
            WHERE 1 = 1
        """
        params = []

        id_filtro = self.funcionarios_map.get(self.combo_filtro.get())
        if id_filtro is not None:
            query += " AND p.id_funcionario = %s"
            params.append(id_filtro)

        texto_data = self.entry_filtro_data.get().strip()
        if texto_data:
            try:
                dia = datetime.strptime(texto_data, FORMATO_DATA).date()
            except ValueError:
                messagebox.showerror("Erro", "Data inválida. Use DD/MM/AAAA.")
                return
            query += " AND DATE(p.data) = %s"
            params.append(dia)

        if not self.var_anuladas.get():
            query += " AND p.anulada = 0"

        query += " ORDER BY p.data DESC"

        try:
            self.cursor.execute(query, params)
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
  
  
  #adicionar picagem
    def adicionar_picagem(self):
        self.formulario("Adicionar picagem manual",
                        None, datetime.now().strtime(FORMATO_DATA),
                        "", None, self. gravar_nova
            
        )
        
        
    #gravar nova picagem
    def gravar_nova(self,id_funcionario,data_hora,tipo,motivo):
        try:
            self.cursor.execute(
                """INSERT INTO( id_funcionario,data,tipo,id_admin_retificacao,motivo_retificacao)
                VALUES (%s, %s, %s, %s, %s) 
                """, (id_funcionario, data_hora, tipo, self.obter_id_admin(), motivo) 
            )
            conn.commit()
        except mysql.connector.Error as erro:
            conn.rollback()
            messagebox.showerror("Erro", f"Erro ao registar picagem: \n{erro}")
            return False
        self.recalcular(id_funcionario,data_hora,tipo)
        self.atualizar_tabela()
        messagebox.showinfo("Sucesso","Picagem registada com sucesso!")
        return True
        
        
        #alterar picagem
    def alterar_picagem(self):
        p= self.obter_selecionada()
        if not p:
            return
        if p["anulada"]:
            messagebox.showerror("Erro", "Esta picagem já está anulada e não pode ser alterada"
                )
            return
        
        #gravar 
    def gravar(id,nova_data,novo_tipo,motivo):
        return self.gravar_alteracao()
    
        self.formulario(
            "Alterar picagem",
            p["nome"],
             p["data"].strftime(FORMATO_DATA),
            p["data"].strftime(FORMATO_HORA),
            p["tipo"],
            gravar
           
    )
    
 #gravar alteracao
    def gravar_alteracao(self,p,nova_data,novo_tipo,motivo): 
        pass
        
        
    def eliminar_picagem(self): pass