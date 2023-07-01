# wallet-monitor
Dero HE Wallet Monitor. Statistics, Sound Notify and more

fork by Berna Cripto: 
+ U$ Fiat amount
+ Sound Notify (coin dropped when blocks found)
+ Remove RPC monitor

This script aims to show some statistics about the Dero mined from a node.
```
------------------------------------------------------------------------------
|          :    1m    :   15m    :    1h    :    6h    :   24h    :    7d    |
|    gain  :  0.0000  :  0.0000  :  0.0000  :  0.0615  :  0.2460  :  2.5854  |
|                                                                            |
| Current height:                                                    1771400 |
| Wallet amount :                                                    7.54695 |
| U$ Fiat amount:                                                      32.07 |
| Date:                                                  2022-03-04 23:25:24 |
------------------------------------------------------------------------------
| 2022-02-25:                                                              0 |
| 2022-02-26:                                                              0 |
| 2022-02-27:                                                         0.0658 |
| 2022-02-28:░░░░░░░                                                  3.7882 |
| 2022-03-01:██████████████████████████████                          14.2731 |
| 2022-03-02:░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░                       15.7479 |
| 2022-03-03:██████████████████████████████████████████████████      23.6838 |
| 2022-03-04:░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░                 18.6378 |
------------------------------------------------------------------------------
```
The information are retrieved by the wallet history and contains only the data about the mining (coinbase tx).
Info are updated every 60 seconds.

Due to some rounding the script is not 100% accurate but it will get better in the future.


## Requirements

1. Python 3
2. A running dero wallet with the --rpc-server on. **This must be the wallet you are mining on or receiving the node reward.** If the wallet close or is terminated the script will terminate as well.
e.g.
```
./dero-wallet-cli-linux-amd64 --unlock --remote --rpc-server
```

Pip library required:
```
pip3 install python-dateutil
pip3 install requests
pip3 install PySimpleGUI
and more
```

## Installation
```
git clone https://github.com/bernaction/dero-cli-wallet-monitor.git
pip3 install -r requirements.txt
```
or just copy and paste derohe_monitor.py

## Usage
run the code with
```
python3 derohe_monitor.py
```

## Notes

1. This script have been tested on linux only, please report any issue with other systems.
2. wait some time after starting your wallet before starting the script. Sometimes the RPC respond with random stuff when is started.
3. In Windows, install official Python Program and make sure the PATH in Windows Settings to run correctly.
