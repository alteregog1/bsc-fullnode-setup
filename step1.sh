#!/bin/sh
echo "========================================================="
echo "=       Updating and installing requirement             ="
echo "========================================================="
apt-get update
apt-get install unzip -y
apt-get install lz4 -y

geth_linux="https://github.com/binance-chain/bsc/releases/download/v1.1.7/geth_linux"
mainnet="https://github.com/binance-chain/bsc/releases/download/v1.1.7/mainnet.zip"
config_toml="https://raw.githubusercontent.com/alteregog1/bsc-fullnode-setup/main/config.toml"

echo "========================================================="
echo "=    1. Downloading GETH LINUX                          ="
echo "========================================================="
wget $geth_linux
echo "========================================================="
echo "=    2. Downloading genesis.json and config.toml        ="
echo "========================================================="
wget $mainnet
echo "========================================================="
echo "=    3. UNZIPING MAINNET                                ="
echo "========================================================="
unzip mainnet.zip
rm ./mainnet.zip
rm ./config.toml
wget $config_toml
echo "========================================================="
echo "=    4. Initiliaze Genesis Node                         ="
echo "========================================================="
chmod 777 ./geth_linux
./geth_linux --datadir ./node init ./genesis.json
echo "========================================================="
echo "=    5. DOWNLOADING SNAPSHOT                            ="
echo "=    Downloading on Background                          ="
echo "========================================================="
echo "========================================================="
echo "=    Please see this link to download your snapshot     ="
echo "=    https://github.com/binance-chain/bsc-snapshots     ="
echo "========================================================="
echo "Input your snapshot endpoint: "
read snapshot_endpoint 
nohup wget -bqc -O geth.tar.lz4 $snapshot_endpoint  &
echo "========================================================="
echo "=    Downloading on background process, please wait     ="
echo "========================================================="
