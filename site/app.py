import os
from flask import Flask, render_template, redirect, url_for, flash, request, session
from pymongo.mongo_client import MongoClient
from neo4j import GraphDatabase
from datetime import datetime
from dotenv import load_dotenv

app = Flask(__name__)
app.secret_key = 'progettonosql'
load_dotenv()

# Connessione al database MongoDB
mongo_client = MongoClient(os.getenv('MONGO_URI')) #connessione a database Atlas
mongo_db = mongo_client.nosqlproject
mongo_collection = mongo_db.books

# Connessione al database Neo4J
neo_uri = os.getenv('NEO4J_URI')
neo_auth = (os.getenv('NEO4J_USERNAME'), os.getenv('NEO4J_PASSWORD'))
neo_drive = GraphDatabase.driver(neo_uri, auth=neo_auth)

LIBRI_PER_PAGINA = 20
PAGINE_PER_PAGINA = 10

def check_login(login):
    records, summary, keys = neo_drive.execute_query(
    "MATCH (u:USER {login: $login}) RETURN u",
    login = login
    )
    if records:
        return True
    else:
        return False
    
def add_book_visit(login, book_title):
    neo_drive.execute_query(
        """
        MATCH (u:USER {login:$login}), (b:BOOK {titolo:$book_title})
        MERGE (u)-[v:VISITA]->(b)
        ON CREATE SET v.volte = 1
        ON MATCH SET v.volte = v.volte + 1
        SET v.ultima_visita = TIMESTAMP()
        """,
        login = login,
        book_title = book_title
    )

def get_book_visits(login, book_title):
    records, summary, keys = neo_drive.execute_query(
    """
    MATCH (u:USER {login:$login}) -[v:VISITA]-> (b:BOOK {titolo:$titolo})
    RETURN v.volte, v.ultima_visita
    """,
    login = login,
    titolo = book_title
    )
    if not records:
        visite = 0
        ultima_visita = 0
    else:
        if records[0]['v.volte'] == None:
            visite = 0
        else:
            visite = records[0]['v.volte']
        if records[0]['v.ultima_visita'] == None:
            ultima_visita = 0
        else:
            stamp = records[0]['v.ultima_visita'] / 1000
            ultima_visita = datetime.fromtimestamp(stamp).strftime('%d-%m-%Y')
    return visite, ultima_visita

@app.route('/')
def index():
    if 'login' in session:
        return redirect(url_for('catalogo'))
    else:
        return redirect(url_for('login_page'))

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        login = request.form['login']
        login_valid = check_login(login)
        if login_valid:
            session['login'] = login
            return redirect(url_for('catalogo'))
        else:
            flash('Login inesistente', 'error')
            return redirect(url_for('login_page'))
    return render_template('login_page.html')

@app.route('/logout')
def logout():
    if 'login' in session:
        session.pop('login')
    if 'ultimo_libro_visitato' in session:
        session.pop('ultimo_libro_visitato')
    return redirect(url_for('login_page'))

@app.route('/catalogo')
def catalogo():
    if 'login' not in session:
        return redirect(url_for('login_page'))
    
    login = session['login']

    pagina = request.args.get('pagina', 1, type=int)
    query = request.args.get('query', None, type=str)

    if query:
        risultato_query = mongo_collection.find({'book_title': {'$regex': query, '$options': 'i'}}, {'book_description':0})
    else:
        risultato_query = mongo_collection.find({}, {'book_description':0})

    # Recupera il numero totale di libri
    num_libri = risultato_query.explain()['executionStats']['nReturned']
    # Calcola il numero totale di pagine
    num_pagine = (num_libri - 1) // LIBRI_PER_PAGINA + 1

    if pagina > num_pagine:
        pagina = num_pagine
    elif pagina <= 0:
        pagina = 1

    # Calcola il numero di gruppo di pagine in cui si trova la pagina attuale
    gruppo_pagina_attuale = (pagina - 1) // PAGINE_PER_PAGINA + 1
    # Determina la prima pagina da mostrare per il gruppo corrente
    prima_pagina_gruppo = (gruppo_pagina_attuale - 1) * PAGINE_PER_PAGINA + 1
    # Calcola l'offset in base alla pagina attuale
    offset = (pagina - 1) * LIBRI_PER_PAGINA
    # Recupera i libri per la pagina attuale
    if offset <= 0:
        libri_pagina = risultato_query.sort('book_title').limit(LIBRI_PER_PAGINA)
    else:
        libri_pagina = risultato_query.sort('book_title').skip(offset).limit(LIBRI_PER_PAGINA)

    return render_template('lista_libri.html', libri=libri_pagina, num_pagine=num_pagine,
                           pagina_attuale=pagina, prima_pagina_gruppo=prima_pagina_gruppo,
                           query=query, pagine_per_pagina=PAGINE_PER_PAGINA)

@app.route('/libro/<book_title>')
def dettaglio_libro(book_title):
    if 'login' not in session:
        return redirect(url_for('login_page'))
    
    login = session['login']

    libro = mongo_collection.find_one({'book_title': book_title})
    if libro == None:
        return redirect(url_for('catalogo'))
    else:
        visite, ultima_visita = get_book_visits(login, book_title)
        if session.get('ultimo_libro_visitato', None) != book_title:
            add_book_visit(login, book_title)
        session['ultimo_libro_visitato'] = book_title
        return render_template('dettaglio_libro.html', libro=libro, visite=visite, ultima_visita=ultima_visita)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
