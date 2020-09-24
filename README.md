# stake-node

Requires python3.7+ with pip

## Task summary

Assuming tip-node has already been set up, the process for stake-node is almost identical.

## For Discord: create a stake notification channel channel

Create a text channel for notification purposes, this channel can be public and will display stakes as they are received. panda-bot must have at least send_message permissions

## Retrieve API key from panda-bot

Run $stakenode command in DM or any channel with panda-bot present

## Set up stake node 

Set up your blockchain node on the same or an alternate VPS 
This wallet should only be used for panda-bot staking (explorers are fine, as there are no existing blockchain transactions)
Keep this node updated and DO NOT make transactions manually

## Git clone and update script

```
cd ~
git clone https://github.com/fat-panda-club/stake-node.git
cd stake-node
sudo apt-get install python3-pip -y
sudo apt-get install python3-setuptools -y
python3 -m pip install -r requirements.txt
vi stake.py
```

Insert values as follows:

| Attribute  | Description |
| ------------- | ------------- |
| BOT_TOKEN | The bot token you have used in tip-node
| CURRENCY_TICKER  | The ticker of your currency registered on panda-bot  |
| PANDA_AUDIT_CHANNEL | This is the SAME as tip node audit channel |
| FAT_PANDA_CLUB_API_KEY  | panda-bot API key which you can obtain with $tipnode  |
| STAKE_NODE_HOST | IP of the stake node |
| STAKE_NODE_PORT | Port number of the stake node |
| STAKE_NODE_RPC_USERNAME | RPC User of the stake node |
| STAKE_NODE_RPC_PASSWORD | RPC Password of the stake node |


The RPC settings are generally set in the daemon config similarly to below:

```
rpcuser=user
rpcpassword=pass
rpcport=123
rpcallowip=1.2.3.4/32 
staking=1
minting=1
```
This IP is the host/VM which will be running the tip-node script. Please make sure staking or minting is ON!

## Create crontask 

Trigger every 5 minutes, replace with path to python3 and script location where applicable

`*/5 * * * * /usr/bin/python3 ~/tip-node/panda_stake_node.py >> ~/panda_stake_node.log 2>&1`

## Notes

The script will communicate panda-bot API on average every 5 minutes, please do not increase the frequency as it will be rejected
If you'd like assistance with setting up please [contact us via Discord](https://discord.gg/Hs57Jg4) 

## Reward assignment

All new balance or transactions to the stake node will be attributed to the rewards pool, even if you make those transactions by hand.
What does this mean? You can also provide additional rewards by injecting to the pool address, or run masternodes on the same node for extra rewards.

Rewards will be distributed to all participating users in the pool, after fee has been taken (you can set fee as 0 - 10%). The fee is directly assigned to the team member which set up the $stakenode.

## Disclaimer

All blockchain transactions are recorded and validated from both project and panda-bot side to avoid potential tampering. Message editing or deletion is recorded by additonal tooling in the Fat Panda Club channel.

The code provided here have been tested and is fully functional as long as the tip node is in sync, it will the be project team's responsibility to ensure the node is maintained and the log (~/panda_stake_node.log) reviewed regularly for anomalies.

