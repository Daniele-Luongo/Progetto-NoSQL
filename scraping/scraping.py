import requests
import pandas as pd
from pymongo.mongo_client import MongoClient
from bs4 import BeautifulSoup

ratings_dict = {
    'One':1,
    'Two':2,
    'Three':3,
    'Four':4,
    'Five':5
}

ROOT_URL = 'https://books.toscrape.com/catalogue/'
SCRAPING_COMPLETED = False

uri = "mongodb+srv://nosqlproject:HCvkK8yc7rrJq2sB@nosql.0cv08n7.mongodb.net/"
client = MongoClient(uri) #connessione a database Atlas
db = client.nosqlproject
db.drop_collection('books_demo') #il database viene eliminato ogni volta che il codice parte
collection = db.books_demo
scraping_url = 'https://books.toscrape.com/catalogue/page-1.html'

page_no = 1
while not SCRAPING_COMPLETED:
  print(f'Inizio scraping pagina {page_no}.')
  scraping_results = []
  page_content = BeautifulSoup(requests.get(scraping_url).content)
  books_list = page_content.find('ol', {'class':'row'})
  for book in books_list.find_all('li'):
    book_title = book.h3.a['title']
    book_price = book.find('p', {'class':'price_color'}).text
    book_info_url = f'{ROOT_URL}{book.a["href"]}'
    book_info_content = BeautifulSoup(requests.get(book_info_url).content)
    try:
      book_description = book_info_content.find('article', {'class':'product_page'}).find('p', {'class':''}).text
    except:
      book_description = 'No description'
    book_category = book_info_content.find('ul', {'class':'breadcrumb'}).find_all('li')[2].a.text
    for rating in ratings_dict.keys():
      if book.find('p', {'class':f'star-rating {rating}'}):
        book_rating = ratings_dict[rating]
        break
      else:
        book_rating = None
    scraping_results.append([book_title, book_price, book_rating, book_category, book_description])
  scraping_dataframe = pd.DataFrame(scraping_results, columns=['book_title', 'book_price', 'book_rating', 'book_category', 'book_description'])
  scraping_dataframe['book_price'] = scraping_dataframe['book_price'].str[1:].astype(float)
  scraping_dataframe['book_description'] = scraping_dataframe['book_description'].str.replace('...more', '', regex=False)
  collection.insert_many(scraping_dataframe.to_dict('records'))
  print(f'Scraping pagina {page_no} completato.')
  if not page_content.find('li', {'class':'next'}):
    SCRAPING_COMPLETED = True
    print('Scraping completato.')
  else:
    next_page_url = page_content.find('li', {'class':'next'}).a['href']
    scraping_url = f'{ROOT_URL}{next_page_url}'
    page_no += 1