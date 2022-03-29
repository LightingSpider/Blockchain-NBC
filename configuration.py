from flask import Flask
from flask_restx import Api
from flask_cors import CORS
import pymongo
from pymongo import errors as pymongo_errors

global db, api, app, message_queue, col
from node import Node

def init(node: Node):

    global db, message_queue

    # Bootstrap
    if node.node_id == '0':
        client = pymongo.MongoClient(host=['localhost:27017'], replicaset='rs0')
    else:
        client = pymongo.MongoClient(host=['[2001:648:2ffe:501:cc00:11ff:fe87:68aa]:27017'], replicaset='rs0')

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
