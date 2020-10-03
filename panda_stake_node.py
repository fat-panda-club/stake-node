import requests
from bitcoinrpc.authproxy import AuthServiceProxy
import discord
import asyncio
import time
import re
import random
import sys
import traceback
from math import isclose
import os

# This should be the same as tip node BOT_TOEKN!
# Do not share this with anyone!
BOT_TOKEN = os.environ["PANDA_AUDIT_TOKEN"]
# This is the currency which you received API key for
CURRENCY_TICKER = os.environ["PANDA_CURRENCY"] # eg. BOO
# Run $stakeonode to retrieve the API key, you must be admin of the project
FAT_PANDA_CLUB_API_KEY = os.environ["PANDA_API_KEY"]
# This is the panda-bot audit channel for logging all transactions
PANDA_AUDIT_CHANNEL = os.environ["PANDA_AUDIT_CHANNEL"]
# IP of target node, 127.0.0.1 for localhost
STAKE_NODE_HOST = os.environ["PANDA_STAKE_HOST"]
# Port of stake node
STAKE_NODE_PORT = os.environ["PANDA_STAKE_PORT"]
# Provide RPC credentials
STAKE_NODE_RPC_USERNAME = os.environ["PANDA_STAKE_USERNAME"]
STAKE_NODE_RPC_PASSWORD = os.environ["PANDA_STAKE_PASSWORD"]


AUDIT_MESSAGE_REGEX = r"^\<\ ([a-z0-9]{3,7}\-\d+)\ \>.*\ unstaked\ ([0-9]+\.[0-9]+?)\ via.*\ to\ ([a-zA-Z0-9]+?)\!$"

client = discord.Client()

@client.event
async def on_error(event, *args, **kwargs):
    print(traceback.format_exc())
    await client.close()
    sys.exit("Discord Error")

@client.event
async def on_ready():
    # Randomize start time, do not remove or you will be rate limited!
    sleep_time = random.randint(1, 299)
    print("Sleeping for %s seconds..." % sleep_time)
    await asyncio.sleep(sleep_time)

    headers = {
        'x-api-key': FAT_PANDA_CLUB_API_KEY,
        'content-type': "application/json",
        'user-agent': "panda-stake-node-%s" % CURRENCY_TICKER.lower()
        }

    # On failure check VPS is able to access target node and RPC credentials are correct
    connection = AuthServiceProxy("http://%s:%s@%s:%s" % \
        ( STAKE_NODE_RPC_USERNAME, STAKE_NODE_RPC_PASSWORD, STAKE_NODE_HOST, STAKE_NODE_PORT) , timeout=10)

    # Customize based on individual daemon
    try:
        current_balance = connection.getbalance()
        recent_transactions = connection.listtransactions("*", 100, 0)
        base_address = connection.getaddressesbyaccount("")
        if len(base_address) == 0:
            base_address = connection.getnewaddress("")
        # base_address = connect.getaccountaddress("")
    except Exception as exception:
        print("Could not connect to daemon: %s" % exception)
        await client.close()
        sys.exit(exception)

    # Submit deposits to panda-bot
    print("Submitting %s tx" % len(recent_transactions))
    url = "https://api.fatpanda.club/stake/%s" % CURRENCY_TICKER.lower()
    payload = {
        "op": "stakes",
        "transactions": recent_transactions,
        "timestamp": int(time.time()),
        "balance": float(current_balance),
        "address": base_address[0]
    }
    response = requests.request("POST", url, headers=headers, json=payload)
    if response.status_code == 200:
        print(response.json())
    elif response.status_code == 429:
        await client.close()
        sys.exit("Rate limited! Please decrease your job frequency and wait a while.")
    else:
        await client.close()
        sys.exit(response.json()['message'])

    # Process operations from panda-bot
    response = requests.request("GET", url, headers=headers)

    if response.status_code != 200:
        await client.close()
        sys.exit(response.json()['message'])
    elif response.status_code == 429:
        await client.close()
        sys.exit("Rate limited! Please decrease your job frequency and wait a while.")
    else:
        response_json = response.json()
        unstakes = response.json()['unstakes']
        panda_audit_channel = client.get_channel(PANDA_AUDIT_CHANNEL)
        project_audit_channel = client.get_channel(response.json()['private_audit_channel'])

        for op in unstakes:
            # Make sure audit messages are correct, for both panda and project
            ### DO NOT CHANGE THIS! This is under project accountability
            project_audit_message = await project_audit_channel.fetch_message(op['private_audit_id'])
            project_audit_validation = re.match(AUDIT_MESSAGE_REGEX, project_audit_message.content.strip())
            panda_audit_message = await panda_audit_channel.fetch_message(op['panda_audit_id'])
            panda_audit_validation = re.match(AUDIT_MESSAGE_REGEX , panda_audit_message.content.strip())

            if not project_audit_validation:
                unstake_message = "< %s-%s > project audit validation failed!" % (op['currency'], op['reference'])

            elif not project_audit_validation.group(1).lower() == "%s-%s" % (CURRENCY_TICKER.lower(), op['reference'].lower()):
                unstake_message = "< %s-%s > project ticker validation failed!" % (op['currency'], op['reference'])

            elif not isclose(float(project_audit_validation.group(2)), op['amount'] + op['fee'], abs_tol=1e-5):

                unstake_message = "< %s-%s > project amount validation failed!\n%0.4f vs %0.4f + %0.4f" % (op['currency'], op['reference'], float(project_audit_validation.group(2)), op['amount'], op['fee'] )

            elif not project_audit_validation.group(3).lower() == op['to_address'].lower():
                unstake_message = "< %s-%s > project address validation failed!" % (op['currency'], op['reference'])

            elif not panda_audit_validation:
                unstake_message = "< %s-%s > panda audit validation failed!" % (op['currency'], op['reference'])

            elif not panda_audit_validation.group(1).lower() == "%s-%s" % (CURRENCY_TICKER.lower(), op['reference'].lower()):
                unstake_message = "< %s-%s > panda ticker validation failed!" % (op['currency'], op['reference'])

            elif not isclose(float(panda_audit_validation.group(2)), op['amount'] + op['fee'], abs_tol=1e-5):
                unstake_message = "< %s-%s > panda amount validation failed!\n%0.4f vs %0.4f + %0.4f" % (op['currency'], op['reference'], float(panda_audit_validation.group(2)), op['amount'], op['fee'] )

            elif not panda_audit_validation.group(3).lower() == op['to_address'].lower():
                unstake_message = "< %s-%s > panda address validation failed!" % (op['currency'], op['reference'])

            else:
                ### ALL CHECKS PERFORMED TO ENSURE AUDIT MESSAGES ARE VALID, ELSE TX IS SKIPPED and NOT PROCESSED
                try:
                    txid = connection.sendtoaddress(op['to_address'], op['amount'])
                    unstake_message = "< %s-%s > unstake sent: %s" % (op['currency'], op['reference'], txid)
                except Exception as exception:
                    txid = 'failed'
                    unstake_message = "< %s-%s > unstake failed! %s" % (op['currency'], op['reference'], exception)
            try:
                await panda_audit_channel.send(content=unstake_message)
                await project_audit_channel.send(content=unstake_message)
            except Exception as exception:
                print("Could not send unstake audit messages due to: %s" % exception)

            op['txid'] = txid
            response = requests.request("POST", url, headers=headers, json=op)


    await client.close()

client.run(BOT_TOKEN)

