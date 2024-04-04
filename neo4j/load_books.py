# MEGLIO ESEGUIRLO SOLO UNA VOLTA

import os
from pymongo.mongo_client import MongoClient
from neo4j import GraphDatabase
from dotenv import load_dotenv
load_dotenv('../.env')

neo_uri = os.getenv('NEO4J_URI')
neo_auth = (os.getenv('NEO4J_USERNAME'), os.getenv('NEO4J_PASSWORD'))
neo_drive = GraphDatabase.driver(neo_uri, auth=neo_auth)
mongo_client = MongoClient(os.getenv('MONGO_URI'))
mongo_db = mongo_client.nosqlproject
mongo_collection = mongo_db.books

mongo_result = mongo_collection.find({}, {'book_title'})
for result in mongo_result:
    neo_drive.execute_query(
    "CREATE (b:BOOK {titolo:$titolo})",
    titolo = result['book_title']
    )