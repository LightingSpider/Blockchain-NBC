from flask_restx import Api
from flask import Flask, request
from flask_restx import Resource, abort
from flask_cors import CORS
from argparse import ArgumentParser

# Get command line arguments
parser = ArgumentParser()
parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
parser.add_argument('-a', '--address', default='127.0.0.1', type=str, help='Network address')
parser.add_argument('-n', '--node_id', default='0', type=str, help='Node ID')
args = parser.parse_args()

# Take the port & address & node_id of the new node
port = args.port
address = args.address
node_id = args.node_id

# Initialize Database Connection
import pymongo
# client = pymongo.MongoClient("mongodb+srv://admin:aekara21@blockchaincluster.l52dj.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
client = pymongo.MongoClient(host=['localhost:27017'], replicaset='rs0')
db = client[f"node_{node_id}"]
message_queue = db['incoming_messages']


class Block(Resource):

    # @jwt_required
    def post(self):

        # Retrieve incoming block
        block = request.json

        # Add the block to the message collection
        message_queue.insert_one({**{"type": "block"}, **block})

        return {'msg': 'Block added successfully'}

class Transaction(Resource):

    # @jwt_required
    def post(self):

        # Retrieve incoming transaction
        transaction = request.json

        # Add the block to the message collection
        message_queue.insert_one({**{"type": "transaction"}, **transaction})

        return {'msg': 'Transaction added successfully'}

# Only for bootstrap node
class InitSettings(Resource):

    # @jwt_required
    def get(self):

        try:
            settings_col = db["info"]
            settings_doc = list(settings_col.find({"_id": "status_doc"}, {"_id": 0}))[0]

            return {
                **{"new_node_id": str(len(settings_doc['ring']))},
                **settings_doc
            }

        except IndexError:
            abort(400, "Bootstrap node has not been configured yet.")

# Only for bootstrap node
class NewNodeArrived(Resource):

    # @jwt_required
    def post(self):

        # Retrieve the new node specs
        new_node_specs = request.json

        # Add the block to the message collection
        message_queue.insert_one({**{"type": "NewNodeArrived"}, **new_node_specs})

        return {'msg': 'NewNodeArrived message added successfully'}

class Ring(Resource):

    # @jwt_required
    def post(self):

        # Retrieve incoming ring
        ring = request.json

        # Add the block to the message collection
        message_queue.insert_one({**{"type": "ring"}, **ring})

        return {'msg': 'Ring added successfully'}

class Chain(Resource):

    # @jwt_required
    def get(self):

        try:

            settings_col = db["info"]
            status_doc = list(settings_col.find({"_id": "status_doc"}, {"_id": 0}))[0]

            return {
                "UTXOs": status_doc["UTXOs"],
                "chain": status_doc["chain"],
                "chain_hash": status_doc["chain_hash"],
                "signature_chain": status_doc["signature_chain"],
                "last_block_timestamp": status_doc["last_block_timestamp"],
                "chain_transaction_ids": status_doc["chain_transaction_ids"]
            }

        except IndexError:
            abort(400, "This node has not any chain yet.")

# .......................................................................................

# Initialize Flask application
app = Flask(__name__)
CORS(app)
api = Api(app=app, version='1.0', title='Blockchain Node Server')

api.add_resource(Block, '/block')
api.add_resource(Transaction, '/transaction')
api.add_resource(Ring, '/ring')
api.add_resource(InitSettings, '/init_settings')
api.add_resource(Chain, '/chain')
api.add_resource(NewNodeArrived, '/new_node_arrived')


if __name__ == '__main__':

    app.run(host=address, port=port, debug=True)
