# Blockchain-NBC

This blockchain supports only transactions of NooBCash Coins and it's architecture is very close to the philosophy of bitcoin blockchain.

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

### Transaction

### Block

### Node

## Codebase Structure

### *node.py*

### *wallet.py*

### *transaction.py*

### *block.py*

### *configuration.py*

### *custom_errors.py*

### *mining.py*

### *server.py*

### *main.py*

### *cli.py*
