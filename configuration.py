from flask import Flask
from flask_restx import Api
from flask_cors import CORS
import pymongo
from pymongo import errors as pymongo_errors
from argparse import ArgumentParser

from firebase_admin import credentials, firestore, initialize_app

global db, api, app, message_queue, col
from node import Node

def init(node: Node):

    global db, message_queue
    client = pymongo.MongoClient(
        "mongodb+srv://admin:aekara21@blockchaincluster.l52dj.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
    db = client[f"node_{node.node_id}"]
    message_queue = db['incoming_messages']

    # Initialize the database by adding one document into a collection
    try:

        db["info"].insert_one({**{
            "_id": "status_doc"
        }, **node.to_dict()})

    except pymongo_errors.DuplicateKeyError:
        print("Info collection already created")

    # Initialize Flask application
    global api, app
    app = Flask(__name__)
    CORS(app)
    api = Api(app=app, version="1.0", title="Blockchain Node Server")

    return app
