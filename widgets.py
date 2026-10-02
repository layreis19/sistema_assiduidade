"""
O QUE ESTE FICHEIRO FAZ?
Funções para criar os elementos básicos do tkinter sempre com o mesmo
aspeto (cores e fontes), em vez de repetir bg=..., fg=..., font=... em
cada página.

- criar_titulo  -> título grande de uma página
- criar_label   -> texto normal (rótulos de formulários, etc.)
- criar_botao   -> botão azul
- criar_entrada -> caixa de texto (ou de senha)

Todas só CRIAM e devolvem o elemento; quem chama faz o .pack()/.grid().

Exemplo:
    import widgets as w
    w.criar_titulo(self, "FUNCIONÁRIOS").pack(pady=15)
    w.criar_label(self, "Nome:").pack()
    self.entry_nome = w.criar_entrada(self)
    self.entry_nome.pack(pady=5)
    w.criar_botao(self, "Adicionar", self.adicionar).pack(pady=10)
"""

import tkinter as tk
import cores

# ── Cores (únicos sítios onde este ficheiro lê o cores.py) ──
COR_FUNDO = cores.CARD
COR_TEXTO = cores.TEXT
COR_BOTAO = cores.BOTAO
COR_BOTAO_ESCURO = cores.BOTAO_DARK
COR_CAMPO = cores.BLUE_VERY_LIGHT
COR_BORDA = getattr(cores, "BORDER", "#C7E3F2")   # já não existe no cores.py
COR_BRANCO = "#FFFFFF"

# ── Fontes ──
FONTE_TITULO = ("Arial", 24)
FONTE_LABEL = ("Arial", 12)
FONTE_BOTAO = ("Arial", 11)
FONTE_ENTRADA = ("Arial", 11)


def _fundo_de(pai):
    """Fundo do pai, para o label ficar com a mesma cor à volta."""
    try:
        return pai.cget("bg")
    except tk.TclError:
        return COR_FUNDO


def criar_titulo(pai, texto, **extra):
    """Título grande. Ex: criar_titulo(self, "RELATÓRIOS").pack(pady=(30, 20))"""
    return tk.Label(pai, text=texto, font=FONTE_TITULO,
                    bg=_fundo_de(pai), fg=COR_TEXTO, **extra)


def criar_label(pai, texto="", negrito=False, cor=None, **extra):
    """
    Texto normal. negrito=True para destacar; cor="green" para mudar a cor.
    `extra` aceita qualquer opção do tk.Label (anchor, justify, ...).
    """
    fonte = FONTE_LABEL + ("bold",) if negrito else FONTE_LABEL
    return tk.Label(pai, text=texto, font=fonte,
                    bg=_fundo_de(pai), fg=cor or COR_TEXTO, **extra)


def criar_botao(pai, texto, comando, largura=None, **extra):
    """Botão azul. largura=15 para botões todos do mesmo tamanho."""
    if largura is not None:
        extra["width"] = largura
    return tk.Button(
        pai, text=texto, command=comando, font=FONTE_BOTAO,
        bg=COR_BOTAO, fg=COR_BRANCO,
        activebackground=COR_BOTAO_ESCURO, activeforeground=COR_BRANCO,
        bd=0, relief="flat", cursor="hand2", padx=14, pady=6, **extra)


def criar_entrada(pai, largura=25, senha=False, **extra):
    """Caixa de texto. senha=True mostra asteriscos em vez do texto."""
    if senha:
        extra["show"] = "*"
    return tk.Entry(
        pai, width=largura, font=FONTE_ENTRADA,
        bg=COR_CAMPO, fg=COR_TEXTO, insertbackground=COR_TEXTO,
        bd=0, highlightthickness=1,
        highlightbackground=COR_BORDA,    # borda normal
        highlightcolor=COR_BOTAO,         # borda quando tem o cursor
        **extra)