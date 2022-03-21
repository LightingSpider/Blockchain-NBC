import pymongo
from argparse import ArgumentParser
import time

# Get command line arguments
parser = ArgumentParser()
parser.add_argument('-n', '--node_id', default='0', type=str, help='Node ID')
parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
parser.add_argument('-a', '--address', default='127.0.0.1', type=str, help='Network address')
args = parser.parse_args()

# Take the port & address & node_id of the new node
port = args.port
address = args.address
node_id = args.node_id

# Initialize Database Connection
client = pymongo.MongoClient("mongodb+srv://admin:aekara21@blockchaincluster.l52dj.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
db = client[f"node_{node_id}"]
message_queue = db['incoming_messages']

def add_transaction(recipient_node_id: str, amount: str):

    message_queue.insert_one({**{"type": "NewTransaction"}, **{
        "recipient_node_id": recipient_node_id,
        "amount": amount
    }})

    print("New transaction added successfully to queue.")


with open(f"/home/airth/Documents/9οeksamino/katanemimena/ergasia/noobcash/transactions/5nodes/transactions{node_id}.txt") as transaction_file:

    cnt = 0
    for line in transaction_file:
        recipient_id = line[2]
        amount = line[4:].replace('\n', '')
        print(f"Transfer {amount} from {node_id} to {recipient_id}")

        time.sleep(10)
        cnt += 1

        if cnt % 10 == 0:
            time.sleep(20)

