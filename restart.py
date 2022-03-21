import pymongo
import os, signal

client = pymongo.MongoClient(
    "mongodb+srv://admin:aekara21@blockchaincluster.l52dj.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")

def clean_db():
    db_names = client.list_database_names()
    for x in db_names:
        if "node" in x:
            print("Delete", x)
            db = client[x]
            client.drop_database(db)


def process():
    # Ask user for the name of process
    name = 'server.py'
    try:

        # iterating through each instance of the process
        for line in os.popen("ps ax | grep " + name + " | grep -v grep"):
            fields = line.split()

            # extracting Process ID from the output
            pid = fields[0]

            # terminating process
            os.kill(int(pid), signal.SIGKILL)
        print("Process Successfully terminated")

    except:
        print("Error Encountered while running script")

process()
clean_db()
