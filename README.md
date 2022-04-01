# Blockchain-NBC

This blockchain supports only transactions of NooBCash Coins and it's architecture is very close to the philosophy of bitcoin blockchain. Some basic assumptions are:
* The network works with a specified number of nodes (N)
* Bootstrap Node starts with 100\*N NBC and gives 100 NBC to every new node which enters the network.
* Bootstrap Node broadcasts the final ring only when all the nodes have arrived.
* Everything is broadcasted (transaction, block, etc.)
* The Consensus algorithm runs only when the previous hash key of the received block is invalid.

## Set-Up

First we need to set-up a local mongoDB Server with a single member ReplicaSet.
There are a lot of ways for doing this. We will see just one of them which works for Ubuntu 21.04

### Download and Intall MongoDB
```
sudo apt update
sudo apt install dirmngr gnupg apt-transport-https ca-certificates software-properties-common
wget -qO - https://www.mongodb.org/static/pgp/server-4.4.asc | sudo apt-key add -
sudo add-apt-repository 'deb [arch=amd64] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/4.4 multiverse'
apt install mongodb-org
```

***Start and Enable the Service***
```
systemctl start mongod
systemctl enable mongod
systemctl status mongod
```

***Set-up the Replica Set***

Open the configuration file
```
sudo vim /etc/mongod.conf
```

Add this line
```
replication:
  replSetName: "rs0"
```

Restart MongoDB
```
sudo systemctl restart mongod
```

Open the mongo shell
```
mongo
```

Initiate Replica set
```
rs.initiate()
```

As for the MongoDB everything is ready and now that we have overcome the difficult point, we are ready to start the blockchain.

First of all, we need to decide some important parameters:
* Number of Nodes (N) 
* Block Capacity (C)
* Level of Difficulty (D)

You can change these parameters from the ```main.py``` at the first lines.

After setting these parameters we are ready to create our bootstrap node.

```
python main.py -a 127.0.0.1 -p 5000
```

With the same way we can create all the other nodes. But we can't exceed the declared number of nodes (N).
Let's create another one which listens on port *5001*.
```
python main.py -a 127.0.0.1 -p 5001
```

After setting-up all the needed nodes we are ready to transfer some money using the CLI.

For example, if we want to transfer 5 NBCs from node 0 to node 1:
```
python cli.py transaction --n 0 1 5
```

and we can check their balance using again the CLI:
```
python cli.py balance --n 0
python cli.py balance --n 1
```

Another function of the CLI is *view* which shows the last validated block of a node's chain.
```
python cli.py view --n 0
```

## The Basic Elements

### Wallet
Each wallet has its own RSA Key object, with a size of 2048 bits, which consists of
by a Public and a Private Key. Also the public address of the wallet is the same
the public key decoded with utf-8.

### Transaction
Each transaction consists of a Receiver & Sender Address and the desired amount, the system also supports float Amount. Next, we define Transaction Inputs that we will explain later how they are created. Having,
so, Sender, Receiver, Amount and Transaction Inputs we can find the Hash Key
of the transaction, which will be its ID. Finally, we define the signature of one
transaction, which is created with the sender's private key, and a timestamp on
time that is created so that we can classify transactions in
out-of-order situations.

### Block
Each block has a Previous Hash Key that shows the last block of the chain in
each node of the network, a creation timestamp that will help us
later in the Consensus Algorithm and a list of Transaction objects.
Hash Key and Nonce are set after the block is mined.
For the same reason as in the transaction, here we have a to_dict () function.
An important function is remove_common_transactions () which subtracts from
current block of each node are the Transactions that have been certified by others
validated broadcasted blocks.

### Node
A node is both a client and a miner, so it has different functions.
The basic attributes are:

* ***network_address***: string
* ***port***: int
* ***node_id***: string
* ***wallet***: Wallet
* ***UTXOs***: {TransactionOutputs}
* ***ring***: dict
* ***chain***: [Block.to_dict ()]
* ***current_block***: Block

#### \_\_init\_\_
* Bootstrap Node:  
  - When we are going to create the bootstrap we follow a different procedure. Specifically:
  - We initialize the ring,
  - We make the first transaction given 100 * N NBCs to bootstrap,
  - We create the Genesis block and put it in the chain,
  - We make our current block,
  - We initialize the UTXOs

* Simple Node: 
  - Any node other than bootstrap.
  - We accept from bootstrap the chain, UTXOs, ring,
  - We verify the chain we received
  - We make our current block

*When we refer to a current block, we mean the block into which all incoming transactions will enter. Once its capacity is reached, we redefine another current block.*

#### General Functions
* ***to_dict ()***, so we can save the node state.

#### Receiver Functions
* ***Add transaction*** to the current block. Here we check each time whether we have reached the block capacity so that we can start mining.
* ***Receive a mined block*** that either comes from the node itself or from someone else. Once we receive a block we automatically validate it, put it in our chain, remove all the common transactions we may have and finally change the previous hash key of our current block.

#### Creating Functions
* ***Create a transaction***. Here we initialize the transaction object and call the sign_transaction (). Then we broadcast it.

* ***Create a new block***. This function is called when we start mining and we are ready to make our new block that will receive the next transactions.

#### Validation Functions
* ***Validate transaction***. This is one of the most important functions of the node as we check the transaction signature, check the transaction hash key and start collecting the necessary UTXOs. Once we see that the necessary amount is covered, we create the Transaction Inputs and the Transaction Outputs and renew the UTXOs accordingly so that we do not have to run the chain every time. Once we go through all these stages we are ready to put the transaction in our current block.

* ***Validate chain***. Here we just check all the blocks in the chain, so basically we just call validate_block ().

* ***Validate block***. Here we control an incoming block either when we have made it or when it comes from another node. The control steps are as follows:
  - We check the hash key to see if the difficulty is satisfied.
  - "Hash" the block again to check if the Nonce (proof-of-work) given to us is correct.
  - We check the previous hash key and if it is not correct we run consensus.
  - We check if it contains transactions that are already in our chain. If so, then we find the non-common ones and process them.

### Broadcasting Functions
* ***Broadcast transaction*** 
* ***Broadcast block***

* ***Broadcast final ring***. This function is only for the Bootstrap node, which sends the final ring to all nodes in the network as soon as they all arrive.

#### Settings & Ring Functions
* ***Register Node to network***. This function can again be called from the bootstrap node and what it does is renew the ring as a new node arrives and automatically sends it 100 NBC. Finally, it checks if it has filled the network, so that it sends the final ring to all the nodes, which it "hashes" and signs as a bootstrap.

* ***Send init settings***. This function gives the initial settings to any new node, such as node_id, current ring, current chain, and UTXOs. Again called only by bootstrap.

* ***Get the final ring***. This function is called by all nodes except bootstrap. It is intended to receive the final ring, but to avoid malicious broadcasting we check the signature and the content of the message, so that we can be sure that we got the right ring.

#### Mining Functions
* ***Mine block***. The secret here is to start mining in parallel so that the whole code is not blocked. ‘If the mining was not done in parallel then each node could not" hear "for other messages and would wait for its mining to end first.
As a result, we would have to constantly call the consensus algorithm. And this would not be at all efficient in terms of performance & bandwidth, but the worst thing is that the system would no longer be decentralized, as in each mining everyone would end up taking someone else's chain.
So, in essence, a subprocess is born that runs mining.py and simply updates the system as soon as it manages to find a Nonce that satisfies the specified Difficulty.

#### Consensus Functions
* ***Resolve conflicts***. This function is called when a new mined block arrives and during the validation process we see that the previous hash keys do not match. Purpose of this function is to request the chain from all other nodes, find the correct one, renew the UTXOs and update the current block.

* ***Ask for chain***. This function simply sends requests to the nodes to request their chain.

* ***Find the right chain***. Here, having gathered all the chains, we sort them by length so as to get the largest validated chain. However, in case we find more chains with the same length, then as a second selection criterion we have the timestamp of the last validated block of the chain.
Therefore, we choose the largest and oldest chain of the system.

## Codebase Structure

The code was written in Python and we used the Flask framework for the rest of the application. We also used MongoDB as a database for better system monitoring.
The whole application consists of the following files:

### node.py: 
Defines the Node class

### wallet.py: 
Defines the Wallet class

### transaction.py: 
Defines the Transaction class

### block.py: 
Defines the Block class

### configuration.py:
Initializes the connection to the database (MongoDB) and
defines the necessary collections in the database, as in MongoDB a collection cannot be defined if it does not contain content.

### custom_errors.py: 
Here we define our own exceptions which are raised at various points in the code, but all are caught in main.py and handled accordingly.

### mining.py: 
This is basically mining, where we try to find the right Nonce, using Crypto.Random.get_random_bytes (64), which satisfies the desired difficulty. Once found, the node is updated with a "FoundNonce" message.

### server.py: 
Here we set up our Flask server and define all our endpoints.

### network.py: 
Here we handle all the requests that our node may want to send to anyone else. When, e.g. wants to broadcast a block or a transaction or e.g. when it wants to request the settings from the bootstrap node.

### main.py: 
This is the file that starts building a node. That is, if a new node wants to enter the network, we will run the command
```python main.py -a <ADDRESS> -p <PORT>```
where address & port are the contact details of the node.
So main.py follows these steps:
* The Wallet is made.
* It tries to communicate with the bootstrap node, so that it receives the necessary initial information. If the communication fails, then this node is * the first on the network and is the bootstrap.
* We create the database for the node and initialize the connection.
* With subprocess.Popen we run server.py to lift the Flask server.
* If the node is not bootstrap, it sends a message to bootstrap informing it that it has successfully entered the network and received 100 NBCs.
Once all this is done, then the node just listens for messages via MongoDB.watch (which is essentially collection streaming).

### cli.py: 
Here we make our CLI for the view, balance & transaction functions. Specifically we use the transaction for the simulations.

## Network & Communications
![Screenshot from 2022-04-01 19-47-48](https://user-images.githubusercontent.com/44092571/161307204-fcb9f8c9-dd4e-4a8e-b038-0f3f21ad8ec4.png)

The image above describes how a node works and how it communicates with the network. In ```main.py``` runs the Node object which manages all the processes and permanently "streams" from its own database all the incoming messages. All message types are as follows:
* "block"
* "transaction"
* "ring"
* "NewNodeArrived"
* "NewTransaction"
* "FoundNonce"

However, not everyone can write to the base of another node and here comes the ```server.py``` which is born at the beginning of node initialization and sets up a flask server. Therefore, this server is responsible for receiving all requests and placing the correct messages in the database in the correct format. This sub-process dies as soon as main.py dies.

Then when the block is full of transactions, then main.py generates a subprocess with Popen, ```mining.py```. The purpose of this is to find the Nonce that satisfies the respective difficulty and as soon as it finds it, it places in the base a message "FoundNonce" that contains all the necessary information for the mined block.

Finally each node sends different requests to the other nodes using simple HTTP requests through the ```network.py``` file.
