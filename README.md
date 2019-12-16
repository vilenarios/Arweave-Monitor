# Arweave-Monitor
Arweave-Monitor is a python script to monitor Arweave nodes to give miners visibility over the decentralized Permaweb.  It will report on various metrics including
- Wallet balances and blocks found
- RAM and Storage usage
- Local and network hash rates
- Network utilization
- Blockweave forks
- Errors
- Other various performance metrics

Optionally, the script includes the capability to send all of this data to a Graphite server, which allows for rich visualization through reporting dashboard tools like Graphana.  

![All node performance example](https://github.com/vilenarios/Arweave-Monitor/blob/master/AllNodePerformance_GrafanaExample.JPG)

![All node metrics example](https://github.com/vilenarios/Arweave-Monitor/blob/master/AllNodeMetrics_GrafanaExample.JPG)


Otherwise, the script is designed to run without any other inputs from the miner, and all information is captured dynamically, local to the node itself.

This script was developed for primary use with Ubuntu 18.04.  While it primarily uses Python3.8, the following prerequisites must be installed for this script to work properly.

sudo apt install software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt install python3.8 -y
sudo apt install python3.8-dev -y
sudo apt install python3-pip -y
sudo python3.8 -m pip install requests
sudo python3.8 -m pip install psutil
Place the arweave-monitor.py script in the root directory for Arweave

It is recommended to configure Arweave-Server and Arweave-Monitor as services, so they both start up automatically on boot up.

Work to be completed
- Add temperature monitor
- Add better network bandwith utilization monitor
- Include other operational capabilities, like restart Arweave-Server if it suffers unrecoverable errors.

Thanks to Gerrit and Marcin for helping me test this!  Please reach out to Vilenarios in the Arweave Mining discord if you have any issues or requests to add functionality.  Although I reserve the right to ignore them :)
