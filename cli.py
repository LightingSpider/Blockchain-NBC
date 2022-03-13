import click
import pymongo

# Connect to database
client = pymongo.MongoClient("mongodb+srv://admin:aekara21@blockchaincluster.l52dj.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")

@click.group()
def cli():
    pass

@cli.command()
@click.argument('recipient_node_id', metavar='recipient_node_id')
@click.argument('amount', metavar='amount')
@click.option('--n', default='0', help='My node ID')
def transaction(recipient_node_id: str, amount: str, n: str):
    """
    Transfer <amount> NBCs to node with id: <recipient_node_id>.
    """

    db = client[f"node_{n}"]
    message_queue = db['incoming_messages']
    message_queue.insert_one({**{"type": "NewTransaction"}, **{
        "recipient_node_id": recipient_node_id,
        "amount": amount
    }})

    click.echo("New transaction added successfully to queue.")

@cli.command()
@click.option('--n', default='0', help='My node ID')
def view(n: str):
    """
    View the transactions contained in the last validated block in the blockchain.
    """
    try:

        db = client[f"node_{n}"]

        # Get the node's current status
        status_col = db["info"]
        status_doc = list(status_col.find({"_id": "status_doc"}, {"_id": 0}))[0]
        transactions = status_doc['chain'][-1]['transactions']

        for x in transactions:
            click.echo(x)
            click.echo('------------------')

    except IndexError:
        click.echo("There is not yet any validated block in the blockchain.")

@cli.command()
@click.option('--n', default='0', help='My node ID')
def balance(n: str):

    """
    Shows the current balance of the wallet.
    """

    try:

        db = client[f"node_{n}"]

        # Get the node's current status
        status_col = db["info"]
        status_doc = list(status_col.find({"_id": "status_doc"}, {"_id": 0}))[0]

        # Get all the node's UTXOs
        wallet_address = status_doc['public_key']
        wallet_UTXOs = status_doc['UTXOs'][wallet_address]

        # Calculate the balance
        wallet_balance = 0.0
        for utxo in wallet_UTXOs.values():
            wallet_balance += float(utxo['amount'])

        click.echo(wallet_balance)

    except Exception as e:
        click.echo('Error with:')
        click.echo(str(e))

if __name__ == '__main__':
    cli()

