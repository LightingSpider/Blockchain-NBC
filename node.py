N = 4
C = 1
DIFF = 5

import json
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from subprocess import Popen

import custom_errors
from block import Block
from wallet import Wallet
import network
from transaction import Transaction

class Node:

	"""
	The chain is a list of blocks in the form of a dictionary
	The ring is a dictionary which contains all the necessary communication information with the other nodes
	The UTXOs is a dictionary with key the public_key of each node and with value a dictionary of TransactionOutputs
	The mining_proc is a value which helps us to understand if the mining process is finished or not
	The block_for_mining is a block.to_dict() which helps us to reverse transactions
	The chain_transaction_ids is a set of transaction ids in order to avoid duplicate transactions in our chain
	"""
	def __init__(self,  wallet: Wallet, chain: [dict], ring: dict, UTXOs: dict, node_id: str = '0', address: str = '127.0.0.1', port: int = 5000):

		self.network_address = address
		self.port = port
		self.node_id = node_id
		self.wallet = wallet
		self.mining_proc = None
		self.block_for_mining = None
		self.chain_transaction_ids = set()

		# Key: Node public addresses
		# Value: List of TransactionOutput.to_dict()
		self.UTXOs = {}

		print('Creating the Node object.')

		# The creation of the boostrap node
		if node_id == '0':

			# The ring is where we store information for every node, as its id, its address (ip:port) and its public key
			# That's why here we only add at the ring the boostrap node
			# It is a dictionary where the key is the id of each node
			self.ring = {
				'0': {
					'address': address,
					'port': port,
					'public_key': self.wallet.address
				}
			}

			# Create the first transaction where the boostrap node takes the first NBCs
			first_transaction = Transaction(
				sender_address='0',
				receiver_address=self.wallet.address,
				amount=str(100.0*N),
				transaction_inputs=[]
			)

			# This transaction does not need validation
			first_transaction.add_transaction_outputs(surplus_amount='0')
			first_transaction.sign_transaction(wallet.private_key)

			# Create the genesis block
			self.current_block = Block(prev_hash='1', transaction_list=[])
			self.current_block.add_transaction(first_transaction)

			# This block contains only the first transaction,
			# and we are ready to find its hash key because we are given the nonce
			nonce = b'0'
			block_bytearray = self.current_block.bytearray_before_nonce()
			block_bytearray.extend(nonce)
			block_hash = SHA256.new(data=block_bytearray)
			self.current_block.is_mined(nonce=nonce, hash_key=block_hash.hexdigest())

			# The genesis block does not need validation and that's why it is added to the chain
			self.chain = [self.current_block.to_dict()]
			self.create_new_block()

			# Now the bootstrap node owns 100*N NBCs
			bootstrap_trans_output = first_transaction.transaction_outputs[0]

			self.UTXOs[self.wallet.address] = {}
			self.UTXOs[self.wallet.address][bootstrap_trans_output.id] = bootstrap_trans_output.to_dict()

		# This is for all the other nodes which are not bootstrap.
		else:

			# We take the current chain from the bootstrap node which means
			self.chain = chain
			self.validate_chain()

			# The node will get the full ring when all the nodes arrive.
			self.ring = ring

			# The node takes the UTXOs from the bootstrap
			self.UTXOs = UTXOs

			# Create the block where all the incoming transactions will be added.
			self.create_new_block()

		print('Node object created, with id: ', node_id)
		print('---------------------------------------')

	# -------------- General  ---------------

	def to_dict(self) -> dict:

		"""
		Find the chain hash in order to sign it,
		we will use these values when there is a conflict in the chain,
		and we need tot avoid malicious chain broadcasting.
		"""

		# First encode the dict into bytearray
		encoded_chain = json.dumps(self.chain).encode('utf-8')
		bytes_chain = bytearray(encoded_chain)

		# Create the hash key based on this bytearray
		hash_chain = SHA256.new(data=bytes_chain)

		# Now create the signature
		signature_chain = pkcs1_15.new(self.wallet.private_key).sign(hash_chain)

		return {
			"address": self.network_address,
			"port": self.port,
			"node_id": self.node_id,
			"ring": self.ring,
			"public_key": self.wallet.address,
			"chain": self.chain,
			"chain_transaction_ids": list(self.chain_transaction_ids),
			"current_block": self.current_block.to_dict(),
			"UTXOs": self.UTXOs,
			"chain_hash": hash_chain.hexdigest(),
			"signature_chain": signature_chain.decode('ISO-8859-1'),
			"last_block_timestamp": self.chain[-1]['timestamp']
		}

	# -------------- Receiver actions --------------

	def add_transaction_to_block(self, transaction: Transaction) -> None:

		# Add it to the current block
		block = self.current_block
		block.add_transaction(transaction)

		# Check if block is full of capacity
		block_current_capacity = len(block.list_of_transactions)
		if block_current_capacity == C:
			print('Block is full.')
			self.mine_block()
			self.create_new_block()

	def receive_block(self, block: dict) -> None:

		trans_amounts = [x['amount'] for x in block['transactions']]
		print(f'Receive block with: {trans_amounts} and with hashKey:')
		print(block['hashKey'])

		# First validate the incoming block
		self.validate_block(block)

		# Add block to our chain
		self.chain.append(block)

		# Remove the common transactions (if they exist)
		self.current_block.remove_common_transactions(block['transactions'])

		# Update the Chain transaction ids, where we keep the ids of all the transactions in our chain
		for trans in block['transactions']:
			self.chain_transaction_ids.add(trans['id'])

	# ---------------- Creation ---------------

	def create_transaction(self, receiver_node_id: str, amount: str) -> None:

		print("Create a transaction")
		print(f"node_{self.node_id} --> node_{receiver_node_id} : {amount} NBCs")

		# Get the public keys
		rec_pub_key = self.ring[receiver_node_id]['public_key']
		send_pub_key = self.wallet.address

		print('Create the transaction object')

		# Create the transaction
		transaction = Transaction(
			sender_address=send_pub_key,
			receiver_address=rec_pub_key,
			amount=amount
		)

		print('Sign the transaction with my private key')

		# Sign the transaction with the sender's private key
		transaction.sign_transaction(self.wallet.private_key)

		print('Transaction object created')
		print('---------------------------------------')

		# Broadcast the transaction to all the other nodes
		self.broadcast_transaction(transaction)

	def create_new_block(self) -> None:

		# Initialize a new empty block
		self.current_block = Block(
			transaction_list=[]
		)

	# ----------------  Validation  ---------------

	'''
	This is one of the most important functions of the whole system
	1. Check the capacity of the block in order to avoid asynchronous block over limit
	2. Create the transaction object with the old timestamp in order to create the same transaction ID
	3. Verify the signature
	4. Verify the hash (which is out transaction_id) 
	5. Check the UTXOs
	6. Check the balance
	7. Add the needed TransactionInputs
	8. Create the 2 TransactionOutputs
	9. Update our UTXOs
	10. Check if this transaction exists in our chain
	'''
	def validate_transaction(self, transaction: dict) -> None:

		# Extract all the necessary information form the transaction
		sender_address = transaction['sender']
		transaction_id = transaction['id']
		signature = transaction['signature'].encode('ISO-8859-1')
		amount = transaction['amount']

		# Find the sender node_id
		sender_node_id = None
		for k, v in self.ring.items():
			if v['public_key'] == sender_address:
				sender_node_id = k
				break

		print(f"Validating new transaction from {sender_node_id} with amount {amount}")

		# Check if the current block has reached its capacity
		block_current_capacity = len(self.current_block.list_of_transactions)
		if block_current_capacity == C:
			print('Something went wrong and the current block has reached its capacity.')
			print('So we will reject for now this transaction and we will try to mine again the current block')
			# self.mine_block()
			return

		# Create the transaction object from the given dictionary
		transaction_object = Transaction(
			sender_address=sender_address,
			receiver_address=transaction['receiver'],
			amount=amount,
			timestamp=transaction['timestamp'],
			signature=signature
		)

		# From the address we can create a public key in order to verify the signature
		sender_public_key = RSA.importKey(extern_key=sender_address)

		# Verify the signature
		pkcs1_15.new(sender_public_key).verify(transaction_object.transaction_id, signature)

		# Check that the transaction_object hash to be the same with the given transaction_id
		if transaction_object.transaction_id.hexdigest() != transaction_id:
			raise custom_errors.InvalidHash(
				err=f"Could not validate the HashKey of the transaction {transaction_id}"
			)

		# Find the UTXOs which can provide a total amount >= needed amount
		# When we use a UTXO we have to remove it from the saved UTXOs
		coins_cnt = 0.0
		input_transactions = []
		for utxo_key, utxo_value in self.UTXOs[sender_address].items():

			# Add the UTXO to input transactions
			print(f"Collect {utxo_value['amount']}")
			coins_cnt += float(utxo_value['amount'])
			input_transactions.append(utxo_key)

			# Check if we have sufficient amount of coins
			if coins_cnt >= float(amount):
				print(f"Needed {amount} and collected {str(coins_cnt)}")
				break

		print('Check the balance')
		surplus = coins_cnt - float(amount)
		if surplus < 0:
			raise custom_errors.InsufficientAmount(
				err="Can't create the transaction. Insufficient amount"
			)

		print('Add the TransactionInputs to the transaction object')
		transaction_object.transaction_inputs = input_transactions

		print('Fix UTXOs')

		# Now we have validated the input transactions we can update our UTXOs
		for input_trans_id in input_transactions:
			del self.UTXOs[sender_address][input_trans_id]

		# At this point we have validated the transaction, and we can produce the transaction outputs
		transaction_object.add_transaction_outputs(surplus_amount=str(surplus))
		for trans_output in transaction_object.transaction_outputs:
			receiver_address = trans_output.receiver_address
			if receiver_address not in self.UTXOs.keys():
				self.UTXOs[receiver_address] = {}
			self.UTXOs[receiver_address][trans_output.id] = trans_output.to_dict()

		# Now check if this transaction is already added in my chain
		if transaction_object.transaction_id.hexdigest() in self.chain_transaction_ids:
			raise custom_errors.TransactionAlreadyAdded(
				err="This transaction is already added in my chain"
			)

		print("Transaction validated")

		self.add_transaction_to_block(transaction_object)

		print('---------------------------------------')

	'''
	Validate the given chain either from the bootstrap node either for the consensus algorithm
	The validate_block is called for all the blocks except the genesis block
	'''
	def validate_chain(self) -> None:

		# Validate each block in the chain which is a list of dicts
		# except the genesis block which is the first block in the chain
		for i in range(1, len(self.chain)):
			block = self.chain[i]

			# Check the validity of the hash_key with the difficulty
			block_hash = block['hashKey']
			if block_hash[0:DIFF] != DIFF * '0':
				raise custom_errors.InvalidHash(
					err="Block hash does not satisfy the difficulty level."
				)

			# Check if the given nonce can produce the given hash
			hash_key = Block.find_hash_key(
				nonce=block['nonce'],
				timestamp=block['timestamp'],
				previous_hash=block['previousHashKey'],
				transactions=block['transactions']
			)
			if hash_key.hexdigest() != block_hash:
				raise custom_errors.InvalidHash(
					err="Invalid block hash. Cannot generate the same hash key with the given nonce number."
				)

			# Check the validity of the prev_hash
			prev_block_hash = self.chain[i-1]['hashKey']
			if prev_block_hash != block['previousHashKey']:
				raise custom_errors.InvalidPreviousHashKey(
					err=f"The given PreviousHashKey: {block['previousHashKey']} of the block with hashKey: {block['hashKey']} is not the same with my previous block."
				)


	'''
	1. Check if the hash_key has the required Difficulty
	2. Check the nonce
	3. Check the previous_hash_key
	4. Check if the block contains transaction which are already added in our chain
	'''
	def validate_block(self, block: dict) -> None:

		# Check the validity of the hash_key with the difficulty
		block_hash = block['hashKey']
		if block_hash[0:DIFF] != DIFF*'0':
			raise custom_errors.InvalidHash(
				err="Block hash does not satisfy the difficulty level."
			)

		# Check if the given nonce can produce the given hash
		hash_key = Block.find_hash_key(
			nonce=block['nonce'],
			timestamp=block['timestamp'],
			previous_hash=block['previousHashKey'],
			transactions=block['transactions']
		)
		if hash_key.hexdigest() != block_hash:
			raise custom_errors.InvalidHash(
				err="Invalid block hash. Cannot generate the same hash key with the given nonce number."
			)

		# Check the validity of the prev_hash
		prev_block_hash = self.chain[-1]['hashKey']
		if prev_block_hash != block['previousHashKey']:
			raise custom_errors.InvalidPreviousHashKey(
				err=f"The given PreviousHashKey: {block['previousHashKey']} of the block with hashKey: {block['hashKey']} is not the same with my previous block."
			)

		# Last check if the block contains transactions which already added in my chain
		my_trans_ids = set()
		for my_block in self.chain:
			for trans in my_block['transactions']:
				my_trans_ids.add(trans['id'])

		new_block_trans_ids = {trans['id'] for trans in block['transactions']}

		common_ids = my_trans_ids.intersection(new_block_trans_ids)

		if len(common_ids) != 0:
			print('Common transactions at block validation')
			print(common_ids)
			raise custom_errors.InvalidBlockCommonTransactions(
				err="Unable to accept this block because contains transactions which already added in my chain",
				block_for_validation=block,
				common_trans_ids=list(my_trans_ids)
			)

	# ---------------- Broadcasting ---------------

	def broadcast_transaction(self, transaction: Transaction) -> None:

		print(f"Start broadcasting the transaction with id {transaction.transaction_id.hexdigest()}")
		print('---------------------------------------')

		# Send the mined transaction to all the other nodes
		for node_id, node in self.ring.items():

			if node_id != self.node_id:
				print(f"Send it: node_{node_id} @ {node['address']}:{str(node['port'])}")
				network.send_transaction(
					address=node['address'],
					port=node['port'],
					transaction=transaction.to_dict()
				)

		print('Send transaction to myself.')
		self.validate_transaction(transaction.to_dict())

		print('---------------------------------------')

	def broadcast_block(self, block_dict: dict) -> None:

		print('Start Block broadcasting')
		print('---------------------------------------')

		# Send the mined block to all the other nodes
		for node_id, node in self.ring.items():

			if node_id != self.node_id:

				print(f"Send it: node_{node_id} @ {node['address']}:{str(node['port'])}")
				network.send_block(
					address=node['address'],
					port=node['port'],
					block=block_dict
				)

		print('Send block to myself.')
		self.receive_block(block_dict)

	'''
	Broadcast the final ring to all the other nodes. 
	This function is only called from the bootstrap only when all the nodes have arrived
	'''
	def broadcast_final_ring(self, signature_ring: str, hash_ring: str) -> None:

		print('Start broadcasting the final ring.')
		print('---------------------------------------')

		# Send the final ring to all the other nodes
		for node_id, node in self.ring.items():

			if node_id != self.node_id:

				print(f"Send it: node_{node_id} @ {node['address']}:{str(node['port'])}")
				network.send_ring(
					address=node['address'],
					port=node['port'],
					ring={
						"ring_dict": self.ring,
						"signature": signature_ring,
						"hash_ring": hash_ring
					}
				)

	# ---------------- Settings & Ring ---------------

	'''
	Only the bootstrap node can add a node to the ring after checking his wallet and ip:port address
	After adding, bootstrap node informs all other nodes and gives the request node an id and 100 NBCs
	'''
	def register_node_to_network(self, address: str, port: int, public_key: str) -> None:

		# Only the bootstrap node can execute this function
		if self.node_id != '0':
			raise custom_errors.UnauthorizedNode(
				err="Only the bootstrap node can execute the function 'register_node_to_network'."
			)

		# Add the node to the ring
		new_node_id = str(len(self.ring))
		self.ring[new_node_id] = {
			'address': address,
			'port': port,
			'public_key': public_key
		}

		# Give the new node 100 NBC
		self.create_transaction(receiver_node_id=new_node_id, amount='100.0')

		# This means that all the nodes have arrived, and we are ready to broadcast the ring
		if int(new_node_id) + 1 == N:

			# Sign the message by the bootstrap node in order to avoid malicious ring broadcasting
			# First encode the dict into bytearray
			encoded_ring = json.dumps(self.ring).encode('utf-8')
			bytes_ring = bytearray(encoded_ring)

			# Create the hash key based on this bytearray
			hash_ring = SHA256.new(data=bytes_ring)

			# Now create the signature
			signature_ring = pkcs1_15.new(self.wallet.private_key).sign(hash_ring)

			# Broadcast:
			# 1. ring      --> 'dict'
			# 2. signature --> 'str' decode the signature with ISO-8859-1
			# 3. hash_ring --> 'str' from hex-digest
			self.broadcast_final_ring(
				signature_ring=signature_ring.decode('ISO-8859-1'),
				hash_ring=hash_ring.hexdigest()
			)

	'''
	Send the node_id, chain, UTXOs and ring to new node came into the network
	'''
	def send_init_settings(self, new_node_id: str) -> None:
		settings = {
			'node_id': new_node_id,
			'ring': self.ring,
			'UTXOs': self.UTXOs,
			'chain': self.chain
		}

		network.send_settings(
			address=self.ring[new_node_id]['address'],
			port=self.ring[new_node_id]['port'],
			settings=settings
		)

	'''
	This is function is used only by simple nodes.
	When all the nodes have arrived, the ring will be broadcast from the bootstrap node.
	So each node has to validate the message and update its ring.
	'''
	def get_the_final_ring(self, ring: dict, signature: str, hash_ring: str) -> None:

		print('Get the final Ring.')
		print('---------------------------------------')

		if self.node_id == '0':
			raise custom_errors.UnauthorizedNode(
				err="The bootstrap cannot take the final ring."
			)

		# Check the validity of the content by comparing the hash keys
		encoded_ring = json.dumps(ring).encode('utf-8')
		bytes_ring = bytearray(encoded_ring)
		temp_hash_ring = SHA256.new(data=bytes_ring)
		if temp_hash_ring.hexdigest() != hash_ring:
			raise custom_errors.InvalidHash(err="Invalid Hash Ring.")

		# Check the validity of the sender by verifying the signature
		bootstrap_public_key = RSA.importKey(extern_key=self.ring['0']['public_key'])
		pkcs1_15.new(bootstrap_public_key).verify(temp_hash_ring, signature.encode('ISO-8859-1'))

		# Update the ring
		self.ring = ring

	# ---------------- Mining ---------------

	'''
	When a block has reached the capacity is ready to find the nonce (proof-of-work).
	We will try random 'nonce' until the hash_key of block meets the requirements 
	We create a new subprocess in order to achieve parallel mining
	'''
	def mine_block(self) -> None:

		print('Start mining')
		print('---------------------------------------')

		# We are ready to mine the block, so set the previous hash key
		self.current_block.previous_hash = self.chain[-1]['hashKey']

		# Get the bytes of the current block
		block_bytearray_before_nonce = self.current_block.bytearray_before_nonce()

		# Start parallel mining at the background
		block_bytearray_before_nonce_str = block_bytearray_before_nonce.decode('utf-8')
		self.block_for_mining = self.current_block.to_dict()
		self.mining_proc = Popen([
			"python", "mining.py",
			"-b", block_bytearray_before_nonce_str,
			"-d", str(DIFF),
			"-n", self.node_id,
			"-bd", json.dumps(self.current_block.to_dict())
		])

	# ---------------- Consensus ---------------

	'''
	This function is called when a node receives a block that it cannot be validated
	because the previous_hash field is not equal to the hash of the previous block. 
	The node asks the other nodes for the length of the blockchain and 
	chooses to adopt this with the longer length.
	'''
	def resolve_conflicts(self) -> None:

		# Ask the other nodes for their chain
		chains = self.ask_for_chain()

		# Find the right chain
		right_chain, right_UTXOs, right_chain_ids = self.find_the_right_chain(chains)

		# Update the chain
		self.chain = right_chain
		# self.UTXOs = right_UTXOs
		self.chain_transaction_ids = set(right_chain_ids)

		# Remove the common transactions between my current block and the blocks of the given chain
		for block in self.chain:
			self.current_block.remove_common_transactions(block['transactions'])

	def ask_for_chain(self) -> dict:

		print('Start asking for chain.')
		print('---------------------------------------')

		chains = {}

		# Ask everybody for their chain except myself
		for node_id, node in self.ring.items():

			print(f"Ask for chain from: node_{node_id} @ {node['address']}:{str(node['port'])}")
			chains[node_id] = network.get_chain(
				address=node['address'],
				port=node['port']
			)

		return chains

	'''
	After getting all the chains from all the nodes in the network,
	we need to find the chain which is:
		1. Valid, 
		2. Longest, 
		3. with the Oldest Block
	'''
	def find_the_right_chain(self, chains: dict) -> tuple:

		print('Trying to find the correct chain.')
		print('---------------------------------------')

		# Sort the keys based on the len(chain) and the timestamp of the last valid block
		sorted_keys = sorted(chains, key=lambda k: (-len(chains[k]['chain']), chains[k]['last_block_timestamp']))

		accepted_chain = None
		accepted_UTXOs = None
		accepted_chain_ids = None
		for node_id in sorted_keys:

			print(f'Checking the chain from node_{node_id}')

			# Try to validate the given chain
			try:
				# Check the validity of the content by comparing the hash keys
				encoded_chain = json.dumps(chains[node_id]['chain']).encode('utf-8')
				bytes_chain = bytearray(encoded_chain)
				temp_hash_chain = SHA256.new(data=bytes_chain)
				if temp_hash_chain.hexdigest() != chains[node_id]['chain_hash']:
					raise custom_errors.InvalidHash(err="Invalid Hash Chain.")

				# Check the validity of the sender by verifying the signature
				sender_public_key = RSA.importKey(extern_key=self.ring[node_id]['public_key'])
				pkcs1_15.new(sender_public_key).verify(
					msg_hash=temp_hash_chain,
					signature=chains[node_id]['signature_chain'].encode('ISO-8859-1')
				)

				# Check now the validity of the blocks in the chain
				# self.chain = chains[node_id]['chain']
				# self.validate_chain()

				# If we reach at this point it means the chain is valid,
				# so stop checking the other chains
				accepted_chain = chains[node_id]['chain']
				accepted_UTXOs = chains[node_id]['UTXOs']
				accepted_chain_ids = chains[node_id]['chain_transaction_ids']
				break

			# Catch all the possible exceptions
			except (
					custom_errors.InvalidHash,
					custom_errors.InvalidPreviousHashKey,
					ValueError
			) as e:
				print(f'Error at validating a given chain --> {str(e)}')
				print('Try the next one')
				pass

		if accepted_chain is not None and accepted_UTXOs is not None:
			print(f'Accepted the chain from the node_{node_id}')
			return accepted_chain, accepted_UTXOs, accepted_chain_ids
		else:
			raise custom_errors.UnableResolveConflict(
				err='Could not find a valid chain. Unable to resolve the conflict.'
			)
