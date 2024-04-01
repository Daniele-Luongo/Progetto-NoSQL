from flask import Flask, render_template, redirect, url_for, request
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

app = Flask(__name__)

# Connessione al database MongoDB
uri = "mongodb+srv://nosqlproject:HCvkK8yc7rrJq2sB@nosql.0cv08n7.mongodb.net/"
client = MongoClient(uri, server_api=ServerApi('1')) #connessione a database Atlas
db = client.nosqlproject
collection = db.books

LIBRI_PER_PAGINA = 20

@app.route('/')
def index():
    return redirect(url_for('catalogo'))

@app.route('/catalogo')
def catalogo():
    # Pagina attuale, predefinita a 1
    pagina = request.args.get('pagina', 1, type=int)

    # Recupera il numero totale di libri
    num_libri = collection.count_documents({})

    # Calcola il numero totale di pagine
    num_pagine = (num_libri - 1) // LIBRI_PER_PAGINA + 1

    if pagina > num_pagine:
        pagina = num_pagine
    elif pagina <= 0:
        pagina = 1

    # Calcola l'offset in base alla pagina attuale
    offset = (pagina - 1) * LIBRI_PER_PAGINA

    # Recupera i libri per la pagina attuale
    libri_pagina = collection.find({}, {'book_title'}).sort('book_title').skip(offset).limit(LIBRI_PER_PAGINA)

    return render_template('lista_libri.html', libri=libri_pagina, num_pagine=num_pagine, pagina_attuale=pagina)

@app.route('/libro/<book_title>')
def dettaglio_libro(book_title):
    libro = collection.find_one({'book_title': book_title})
    return render_template('dettaglio_libro.html', libro=libro)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
