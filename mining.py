from argparse import ArgumentParser
from Crypto.Random import get_random_bytes
from Crypto.Hash import SHA256
import json
import os

# Get command line arguments
parser = ArgumentParser()
parser.add_argument('-b', '--block_bytearray_str', default=None, type=str)
parser.add_argument('-bd', '--block_dict_str', default=None, type=str, help='The block_dict as a string in format of bytes')
parser.add_argument('-d', '--diff', default=None, type=int)
parser.add_argument('-n', '--node_id', default=None, type=str, help='Node ID')

args = parser.parse_args()
block_bytearray_str = args.block_bytearray_str
DIFF = args.diff
node_id = args.node_id

# Create the block_dict
block_dict = json.loads(args.block_dict_str)

# Initialize Database Connection
import pymongo
client = pymongo.MongoClient(host=['localhost:27017'], replicaset='rs0')
db = client[f"node_{node_id}"]
message_queue = db['incoming_messages']

# Start mining
block_bytearray_before_nonce = block_bytearray_str.encode('utf-8')
print('START MINING...')
print("---------------------------------------")
while True:

    # Find a random nonce (in bytes)
    nonce = get_random_bytes(64)

    # Add the nonce to the bytearray
    temp_bytearray = bytearray()
    temp_bytearray.extend(block_bytearray_before_nonce)
    temp_bytearray.extend(nonce)

    # Hash the block with SHA256
    block_hash = SHA256.new(data=temp_bytearray)

    if block_hash.hexdigest()[0:DIFF] == DIFF * "0":
        print("FOUND nonce:", block_hash.hexdigest())
        print("---------------------------------------")

        block_dict['nonce'] = nonce.decode('ISO-8859-1')
        block_dict['hashKey'] = block_hash.hexdigest()
        message_queue.insert_one({**{"type": "FoundNonce"}, **{"block_dict": block_dict}})

        break

# Kill myself
os.system(f"kill {str(os.getpid())}")
