from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = "chave_super_secreta_123"


def conectar():
    conn = sqlite3.connect("clientes.db")
    return conn


def criar_banco():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT NOT NULL UNIQUE,
            senha TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            telefone TEXT,
            email TEXT
        )
    """)

    cursor.execute("SELECT * FROM usuarios WHERE usuario = ?", ("admin",))
    usuario = cursor.fetchone()

    if not usuario:
        cursor.execute(
            "INSERT INTO usuarios (usuario, senha) VALUES (?, ?)",
            ("admin", "1234")
        )

    conn.commit()
    conn.close()


@app.route("/")
def inicio():
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    erro = None

    if request.method == "POST":
        usuario = request.form["usuario"]
        senha = request.form["senha"]

        conn = conectar()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM usuarios WHERE usuario = ? AND senha = ?",
            (usuario, senha)
        )
        user = cursor.fetchone()
        conn.close()

        if user:
            session["usuario"] = usuario
            return redirect(url_for("dashboard"))
        else:
            erro = "Usuário ou senha inválidos."

    return render_template("login.html", erro=erro)


@app.route("/dashboard")
def dashboard():
    if "usuario" not in session:
        return redirect(url_for("login"))

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM clientes")
    total_clientes = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "dashboard.html",
        usuario=session["usuario"],
        total_clientes=total_clientes
    )


@app.route("/clientes", methods=["GET", "POST"])
def clientes():
    if "usuario" not in session:
        return redirect(url_for("login"))

    conn = conectar()
    cursor = conn.cursor()

    if request.method == "POST":
        nome = request.form["nome"]
        telefone = request.form["telefone"]
        email = request.form["email"]

        if nome.strip():
            cursor.execute(
                "INSERT INTO clientes (nome, telefone, email) VALUES (?, ?, ?)",
                (nome, telefone, email)
            )
            conn.commit()

    busca = request.args.get("busca", "").strip()

    if busca:
        cursor.execute("""
            SELECT * FROM clientes
            WHERE nome LIKE ? OR telefone LIKE ? OR email LIKE ?
            ORDER BY id DESC
        """, (f"%{busca}%", f"%{busca}%", f"%{busca}%"))
    else:
        cursor.execute("SELECT * FROM clientes ORDER BY id DESC")

    lista_clientes = cursor.fetchall()
    conn.close()

    return render_template(
        "clientes.html",
        clientes=lista_clientes,
        busca=busca
    )


@app.route("/excluir/<int:id>")
def excluir(id):
    if "usuario" not in session:
        return redirect(url_for("login"))

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM clientes WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    return redirect(url_for("clientes"))


@app.route("/logout")
def logout():
    session.pop("usuario", None)
    return redirect(url_for("login"))


if __name__ == "__main__":
    criar_banco()
    app.run(debug=True)