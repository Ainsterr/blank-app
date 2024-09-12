import tkinter as tk
from tkinter import messagebox
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials, firestore
import telebot

# Inicialize o bot com seu token
TOKEN = '7326033429:AAGxoI4BpFwySMekKkPMGk6KNmAq1PpiMXk'
bot = telebot.TeleBot(TOKEN)
CHAT_ID = '-1002167125732'

# Inicialize o Firebase
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Função para salvar os dados dos usuários no Firestore
def salvar_dados_usuario(id_usuario, validade, telefone, unidade_tempo):
    data_inicio = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data_fim = (datetime.now() + timedelta(**{unidade_tempo: validade})).strftime("%Y-%m-%d %H:%M:%S")
    
    # Cria um documento no Firestore
    db.collection("usuarios").document(id_usuario).set({
        "data_inicio": data_inicio,
        "data_fim": data_fim,
        "telefone": telefone,
        "id_usuario": id_usuario
    })

    messagebox.showinfo("Sucesso", f"Acesso criado para o usuário {id_usuario} com validade de {validade} {unidade_tempo}.")

# Função para remover o usuário do grupo no Telegram
def remover_usuario_grupo(id_usuario):
    try:
        bot.kick_chat_member(CHAT_ID, id_usuario)
        bot.unban_chat_member(CHAT_ID, id_usuario)
        messagebox.showinfo("Remover", f"Usuário {id_usuario} foi removido do grupo.")
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao remover o usuário {id_usuario}: {str(e)}")

# Função para remover o usuário do Firestore
def remover_usuario(id_usuario):
    doc_ref = db.collection("usuarios").document(id_usuario)
    doc = doc_ref.get()
    if doc.exists:
        doc_ref.delete()
        remover_usuario_grupo(id_usuario)
        messagebox.showinfo("Sucesso", f"Usuário {id_usuario} removido com sucesso.")
    else:
        messagebox.showwarning("Erro", "Usuário não encontrado.")

# Função para verificar se há usuários com acesso expirado
def verificar_acessos_expirados():
    agora = datetime.now()
    usuarios_ref = db.collection("usuarios")
    expirados = []
    
    # Verificar cada usuário
    for doc in usuarios_ref.stream():
        data_fim = datetime.strptime(doc.to_dict().get('data_fim', ''), "%Y-%m-%d %H:%M:%S")
        if data_fim and agora > data_fim:
            expirados.append(doc.id)
    
    # Remover usuários expirados
    for id_usuario in expirados:
        remover_usuario(id_usuario)

# Função para exibir o tempo restante de acesso
def verificar_tempo_restante(id_usuario):
    doc_ref = db.collection("usuarios").document(id_usuario)
    doc = doc_ref.get()
    if doc.exists():
        data_fim = datetime.strptime(doc.to_dict().get('data_fim', ''), "%Y-%m-%d %H:%M:%S")
        agora = datetime.now()
        restante = data_fim - agora
        messagebox.showinfo("Tempo Restante", f"O tempo restante de acesso para {id_usuario} é de {restante}.")
    else:
        messagebox.showwarning("Erro", "Usuário não encontrado.")

# Função para pesquisar acessos por telefone
def pesquisar_por_telefone(telefone):
    usuarios_ref = db.collection("usuarios").where("telefone", "==", telefone)
    docs = usuarios_ref.stream()
    
    resultados = []
    for doc in docs:
        resultados.append(doc.to_dict())

    if resultados:
        return resultados
    else:
        return None

# Função para renovar o acesso de um usuário
def renovar_acesso(id_usuario, validade, unidade_tempo):
    doc_ref = db.collection("usuarios").document(id_usuario)
    doc = doc_ref.get()
    if doc.exists():
        data_inicio = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data_fim = (datetime.now() + timedelta(**{unidade_tempo: validade})).strftime("%Y-%m-%d %H:%M:%S")
        doc_ref.update({
            "data_inicio": data_inicio,
            "data_fim": data_fim
        })
        messagebox.showinfo("Sucesso", f"Acesso do usuário {id_usuario} renovado com validade de {validade} {unidade_tempo}.")
    else:
        messagebox.showwarning("Erro", "Usuário não encontrado.")

# Interface Gráfica com Tkinter
class PainelAdmin:
    def __init__(self, root):
        self.root = root
        self.root.title("Painel Admin")
        self.root.geometry("600x600")
        self.root.configure(bg="#f0f0f0")

        # Título
        self.label_titulo = tk.Label(root, text="Gerenciamento de Acessos", font=("Helvetica", 16), bg="#4CAF50", fg="white", pady=10)
        self.label_titulo.pack(fill="x")

        # Entrada de ID do usuário
        self.label_id = tk.Label(root, text="ID do Usuário:", font=("Helvetica", 12), bg="#f0f0f0")
        self.label_id.pack(pady=10)
        self.entry_id = tk.Entry(root, font=("Helvetica", 12), width=30)
        self.entry_id.pack()

        # Entrada de tempo de acesso
        self.label_tempo = tk.Label(root, text="Validade (em):", font=("Helvetica", 12), bg="#f0f0f0")
        self.label_tempo.pack(pady=10)
        self.entry_tempo = tk.Entry(root, font=("Helvetica", 12), width=30)
        self.entry_tempo.pack()

        # Entrada de telefone
        self.label_telefone = tk.Label(root, text="Telefone:", font=("Helvetica", 12), bg="#f0f0f0")
        self.label_telefone.pack(pady=10)
        self.entry_telefone = tk.Entry(root, font=("Helvetica", 12), width=30)
        self.entry_telefone.pack()

        # Unidade de tempo
        self.label_unidade_tempo = tk.Label(root, text="Unidade de Tempo:", font=("Helvetica", 12), bg="#f0f0f0")
        self.label_unidade_tempo.pack(pady=10)
        self.var_unidade_tempo = tk.StringVar(value="hours")
        self.option_unidade_tempo = tk.OptionMenu(root, self.var_unidade_tempo, "minutes", "hours", "days")
        self.option_unidade_tempo.pack()

        # Botão para criar acesso
        self.btn_criar_acesso = tk.Button(root, text="Criar Acesso", font=("Helvetica", 12), bg="#4CAF50", fg="white", command=self.criar_acesso)
        self.btn_criar_acesso.pack(pady=20)

        # Botão para remover usuário
        self.btn_remover = tk.Button(root, text="Remover Usuário", font=("Helvetica", 12), bg="#F44336", fg="white", command=self.remover_usuario)
        self.btn_remover.pack(pady=10)

        # Botão para verificar acessos expirados
        self.btn_verificar = tk.Button(root, text="Verificar Acessos Expirados", font=("Helvetica", 12), bg="#FFC107", command=verificar_acessos_expirados)
        self.btn_verificar.pack(pady=10)

        # Botão para verificar tempo restante
        self.btn_tempo_restante = tk.Button(root, text="Verificar Tempo Restante", font=("Helvetica", 12), bg="#2196F3", command=self.verificar_tempo_restante)
        self.btn_tempo_restante.pack(pady=10)

        # Botão para gerenciar acessos
        self.btn_gerenciar_acessos = tk.Button(root, text="Gerenciar Acessos", font=("Helvetica", 12), bg="#9C27B0", fg="white", command=self.gerenciar_acessos)
        self.btn_gerenciar_acessos.pack(pady=20)

    def criar_acesso(self):
        id_usuario = self.entry_id.get()
        validade = self.entry_tempo.get()
        telefone = self.entry_telefone.get()
        unidade_tempo = self.var_unidade_tempo.get()

        if id_usuario and validade.isdigit() and telefone:
            salvar_dados_usuario(id_usuario, int(validade), telefone, unidade_tempo)
        else:
            messagebox.showwarning("Erro", "Por favor, insira todos os dados corretamente.")

    def remover_usuario(self):
        id_usuario = self.entry_id.get()
        if id_usuario:
            remover_usuario(id_usuario)
        else:
            messagebox.showwarning("Erro", "Por favor, insira o ID do usuário.")

    def verificar_tempo_restante(self):
        id_usuario = self.entry_id.get()
        if id_usuario:
            verificar_tempo_restante(id_usuario)
        else:
            messagebox.showwarning("Erro", "Por favor, insira o ID do usuário.")

    def gerenciar_acessos(self):
        self.abrir_painel_acessos()

    def abrir_painel_acessos(self):
        # Implementar painel de gerenciamento de acessos (opcional)
        pass

# Inicializa a interface Tkinter
root = tk.Tk()
app = PainelAdmin(root)
root.mainloop()
