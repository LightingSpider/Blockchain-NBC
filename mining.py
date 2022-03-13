from argparse import ArgumentParser
from Crypto.Random import get_random_bytes
from Crypto.Hash import SHA256
import os

# Get command line arguments
parser = ArgumentParser()
parser.add_argument('-b', '--block_bytearray_str', default=None, type=str)
parser.add_argument('-d', '--diff', default=None, type=int)
parser.add_argument('-n', '--node_id', default=None, type=str, help='Node ID')
args = parser.parse_args()
block_bytearray_str = args.block_bytearray_str
DIFF = args.diff
node_id = args.node_id

# Initialize Database Connection
import pymongo
client = pymongo.MongoClient(
        "mongodb+srv://admin:aekara21@blockchaincluster.l52dj.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
db = client[f"node_{node_id}"]
message_queue = db['incoming_messages']

# Start mining
block_bytearray_before_nonce = block_bytearray_str.encode('utf-8')
while True:

    # Find a random nonce (in bytes)
    nonce = get_random_bytes(64)

    print("Try nonce")

    # Add the nonce to the bytearray
    temp_bytearray = bytearray()
    temp_bytearray.extend(block_bytearray_before_nonce)
    temp_bytearray.extend(nonce)

    # Hash the block with SHA256
    block_hash = SHA256.new(data=temp_bytearray)

    print("Hash Block:", block_hash.hexdigest())
    print("---------------------------------------")

    if block_hash.hexdigest()[0:DIFF] == DIFF * "0":
        print("FOUND nonce:", nonce)
        print("---------------------------------------")

        # Add the block to the message collection
        message_queue.insert_one({**{"type": "FoundNonce"}, **{
            "nonce": nonce.decode('ISO-8859-1'),
            "hashKey": block_hash.hexdigest()
        }})
        break

# Kill myself
os.system(f"kill {str(os.getpid())}")
