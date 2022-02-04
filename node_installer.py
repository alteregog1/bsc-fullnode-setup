import os
import math
import stat
import sys
import requests
from zipfile import ZipFile
import subprocess
from subprocess import STDOUT
from pathlib import Path


def subprocess_command(command):
    proc = subprocess.Popen(command, shell=True, stdin=None, stdout=subprocess.PIPE, stderr=STDOUT,
                            executable="/bin/bash")
    while proc.poll() is None:
        l = proc.stdout.readline()
        sys.stdout.write(Fore.WHITE + l.decode("utf-8").strip() + "\r")
        sys.stdout.flush()
    proc.wait()
    sys.stdout.write("\n")


try:

    from colorama import init
    from colorama import Fore, Back, Style
except:
    subprocess_command('pip install colorama')

    from colorama import init
    from colorama import Fore, Back, Style


class InstallState():
    UPDATE_OS = "UPDATE_OS"
    INSTALL_PIP = "INSTALL_PIP"
    DOWNLOAD_SETUP_FILES = "DOWNLOAD_SETUP_FILES"
    INITIALIZE_GENESIS = "INITIALIZE_GENESIS"
    DOWNLOADING_SNAPSHOT = "DOWNLOADING_SNAPSHOT"
    EXTRACT_SNAPSHOT = "EXTRACT_SNAPSHOT"
    MOVING_SNAPSHOT = "MOVING_SNAPSHOT"
    CREATE_START_SH = "CREATE_START_SH"
    CREATE_NODE_SERVICE = "CREATE_NODE_SERVICE"
    INSTALL_STATUS = "INSTALL_STATUS"
    CREATE_NODE_CONNECTION = "CREATE_NODE_CONNECTION"

    PENDING = "PENDING"
    DONE = "DONE"


if not os.path.exists("install.log"):
    open("install.log", "w")


class InstallLog():
    def __init__(self, state):
        super().__init__()
        self.state = state

    def check_state(self):
        with open("install.log", "r") as f:
            lines = f.readlines()
            for line in lines:
                if self.state in line:
                    if "DONE" in line:
                        return True
                    else:
                        return False

    def add_state(self, status):
        state_done = f"{self.state}=DONE"
        state_pending = f"{self.state}=PENDING"
        with open("install.log", "r") as f:
            data = f.read()

            if self.state in data:
                data = data.replace(state_pending, state_done)

                with open("install.log", "w") as f:
                    f.write(data)
            else:
                with open("install.log", "a") as f:
                    f.write(f"{self.state}={status}\n")


if not InstallLog(InstallState.UPDATE_OS).check_state():
    InstallLog(InstallState.UPDATE_OS).add_state(InstallState.PENDING)
    print(Fore.GREEN + "=================================")
    print(Fore.GREEN + "|    0. UPDATING OS   |")
    print(Fore.GREEN + "=================================")
    print("")
    subprocess_command("apt-get update")
    subprocess_command("apt-get install lz4 -y")

    InstallLog(InstallState.UPDATE_OS).add_state(InstallState.DONE)

try:
    from tqdm import tqdm
    from bs4 import BeautifulSoup
    from lxml import etree
    import lz4.frame
    import wget
except:

    if not InstallLog(InstallState.INSTALL_PIP).check_state():
        InstallLog(InstallState.INSTALL_PIP).add_state(InstallState.PENDING)
        print(Fore.GREEN + "=================================")
        print(Fore.GREEN + "|    00. INSTALLING PYTHON PIP   |")
        print(Fore.GREEN + "=================================")
        print("")
        subprocess_command('apt-get install -y python3-pip')

        InstallLog(InstallState.INSTALL_PIP).add_state(InstallState.DONE)

    print(Fore.GREEN + "===========================================")
    print(Fore.GREEN + "|    000. INSTALLING PYTHON REQUIREMENTS   |")
    print(Fore.GREEN + "===========================================")
    print("")
    subprocess_command('pip install tqdm')
    subprocess_command('pip install bs4')
    subprocess_command('pip install lxml')
    subprocess_command('pip install lz4')
    subprocess_command('pip install wget')

    from tqdm import tqdm
    from bs4 import BeautifulSoup
    from lxml import etree
    import lz4.frame
    import wget

init()

geth_linux = "https://github.com/binance-chain/bsc/releases/download/v1.1.7/geth_linux"
mainnet = "https://github.com/binance-chain/bsc/releases/download/v1.1.7/mainnet.zip"
config_toml = "https://raw.githubusercontent.com/briliant1/bsc-fullnode-setup/main/config.toml"
bsc_snapshot = "https://github.com/binance-chain/bsc-snapshots"
cur_dir = os.path.dirname(__file__)
permission = stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IWOTH | stat.S_IXOTH


def unzip_file(path):
    with ZipFile(file=path) as zip_file:
        for file in tqdm(iterable=zip_file.namelist(), total=len(zip_file.namelist())):
            zip_file.extract(member=file)


def convert_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])


class Downloader():
    def downloader(self, url: str, output: str, resume_byte_pos: int = None):
        # Get size of file
        r = requests.head(url)
        file_size = int(r.headers.get('content-length', 0))

        # Append information to resume download at specific byte position
        # to header
        resume_header = ({'Range': f'bytes={resume_byte_pos}-'}
                         if resume_byte_pos else None)

        # Establish connection
        r = requests.get(url, stream=True, headers=resume_header)

        # Set configuration
        block_size = 1024
        initial_pos = resume_byte_pos if resume_byte_pos else 0
        mode = 'ab' if resume_byte_pos else 'wb'
        file = Path(output)

        with open(file, mode) as f:
            with tqdm(total=file_size, unit='B',
                      unit_scale=True, unit_divisor=1024,
                      desc=file.name, initial=initial_pos,
                      ascii=True, miniters=1) as pbar:
                for chunk in r.iter_content(32 * block_size):
                    f.write(chunk)
                    pbar.update(len(chunk))

    def download(self, url: str, output: str) -> None:
        # Establish connection to header of file
        r = requests.head(url)

        # Get filesize of online and offline file
        file_size_online = int(r.headers.get('content-length', 0))
        file = Path(output)

        if file.exists():
            file_size_offline = file.stat().st_size

            if file_size_online != file_size_offline:
                print(f'File {file} ({convert_size(file_size_online)}) is incomplete. Resume download.')
                self.downloader(url, output, file_size_offline)
            else:
                print(f'File {file} ({convert_size(file_size_online)}) is complete. Skip download.')
                pass
        else:
            print(f'File {file} ({convert_size(file_size_online)}) does not exist. Start download.')
            self.downloader(url, output)


def get_snapshot_endpoint(location):
    HEADERS = ({'User-Agent':
                    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 \
                (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36',
                'Accept-Language': 'en-US, en;q=0.5'})
    webpage = requests.get(bsc_snapshot, headers=HEADERS)
    soup = BeautifulSoup(webpage.content, "html.parser")
    dom = etree.HTML(str(soup))

    if location == "asia":
        return dom.xpath('//*[@id="readme"]/div[2]/article/p[3]/a')[0].attrib['href']
    elif location == "eu":
        return dom.xpath('//*[@id="readme"]/div[2]/article/p[4]/a')[0].attrib['href']
    elif location == "us":
        return dom.xpath('//*[@id="readme"]/div[2]/article/p[5]/a')[0].attrib['href']


def create_start_node():
    with open("start.sh", "w") as f:
        f.write('./geth_linux --config ./config.toml --datadir ./mainnet --cache 18000 --rpc.allow-unprotected-txs --txlookuplimit 0 --http --maxpeers 150 --ws --syncmode=full --snapshot=true --diffsync --graphql --graphql.vhosts "0.0.0.0"')


def create_node_service():
    data = f"""[Unit]
    Description=BSC Full Node

    [Service]
    User=root
    Type=simple
    WorkingDirectory={cur_dir}
    ExecStart=/bin/bash {cur_dir}/start.sh
    Restart=on-failure
    RestartSec=30
    TimeoutSec=300
    IOWeight=8000
    CPUWeight=8000

    [Install]
    WantedBy=default.target
    """
    with open("/usr/lib/systemd/system/geth_bsc.service", "w") as f:
        f.write(data)


def create_connection():
    with open("node-sync.sh", "w") as f:
        f.write('./geth_linux attach ./mainnet/geth.ipc --exec "eth.syncing"')
        f.close()

    with open("block-check.sh", "w") as f:
        f.write('./geth_linux attach ./mainnet/geth.ipc --exec "eth.syncing.highestBlock - eth.syncing.currentBlock"')
        f.close()

    os.chmod("node-sync.sh", permission)
    os.chmod("block-check.sh", permission)
    subprocess_command(f"ln -s {cur_dir}/node-sync.sh /usr/bin/node-sync")
    subprocess_command(f"ln -s {cur_dir}/block-check.sh /usr/bin/block-check")


if not InstallLog(InstallState.DOWNLOAD_SETUP_FILES).check_state():

    InstallLog(InstallState.DOWNLOAD_SETUP_FILES).add_state(InstallState.PENDING)

    print(Fore.GREEN + "================================")
    print(Fore.GREEN + "|    1. DOWNLOADING SETUP FILES   |")
    print(Fore.GREEN + "================================")

    if not os.path.exists("geth_linux"):
        print(Fore.YELLOW + "|----------[ Downloading geth_linux ]----------|")
        Downloader().download(geth_linux, "geth_linux")
        os.chmod("./geth_linux", permission)
        print("")

    if not os.path.exists("mainnet.zip"):
        print(Fore.YELLOW + "|----------[ Downloading mainnet.zip ]----------|")
        Downloader().download(mainnet, "mainnet.zip")
        os.chmod("./mainnet.zip", permission)
        print("")
        print(Fore.YELLOW + "|----------[ extracting mainnet.zip ]----------|")
        unzip_file("mainnet.zip")
        print("")

    if not os.path.exists("config.toml"):
        print(Fore.YELLOW + "|----------[ Downloading config.toml ]----------|")
        Downloader().download(config_toml, "config.toml")
        os.chmod("./config.toml", permission)
        print("")

    InstallLog(InstallState.DOWNLOAD_SETUP_FILES).add_state(InstallState.DONE)

if not InstallLog(InstallState.INITIALIZE_GENESIS).check_state():
    InstallLog(InstallState.INITIALIZE_GENESIS).add_state(InstallState.PENDING)

    print(Fore.GREEN + "===================================")
    print(Fore.GREEN + "|    2. INITIALIZE GENESIS NODE   |")
    print(Fore.GREEN + "===================================")
    subprocess_command(
        "./geth_linux --datadir ./mainnet init ./mainnet/genesis.json")

    InstallLog(InstallState.INITIALIZE_GENESIS).add_state(InstallState.DONE)

    if not InstallLog(InstallState.DOWNLOADING_SNAPSHOT).check_state():

        InstallLog(InstallState.DOWNLOADING_SNAPSHOT).add_state(InstallState.PENDING)

        print(Fore.GREEN + "================================")
        print(Fore.GREEN + "|    3. DOWNLOADING SNAPSHOT   |")
        print(Fore.GREEN + "================================")
        print("")
        print("Please select snapshot location: ")
        print("1. Asia")
        print("2. EU")
        print("3. US")
        endpoint_location_select = input("Input your choice: ")

        if endpoint_location_select == "1":
            snapshot_url = get_snapshot_endpoint("asia")
        elif endpoint_location_select == "2":
            snapshot_url = get_snapshot_endpoint("eu")
        elif endpoint_location_select == "3":
            snapshot_url = get_snapshot_endpoint("us")

        print(Fore.YELLOW + "|----------[ Downloading Snapshot ]----------|")
        print(f"{Fore.RED}This will take a few hours, please don't close your terminal session")
        Downloader().download(snapshot_url, "snapshot.tar.lz4")
        print("")

        InstallLog(InstallState.DOWNLOADING_SNAPSHOT).add_state(InstallState.DONE)

        if not InstallLog(InstallState.EXTRACT_SNAPSHOT).check_state():
            InstallLog(InstallState.EXTRACT_SNAPSHOT).add_state(InstallState.PENDING)

            print("|----------[ Extracting Snapshot ]----------|")
            print(f"{Fore.RED}This will take a few hours, please don't close your terminal session")
            subprocess_command("lz4 -d snapshot.tar.lz4 | tar -xv")
            print("")

            InstallLog(InstallState.EXTRACT_SNAPSHOT).add_state(InstallState.DONE)

        if not InstallLog(InstallState.MOVING_SNAPSHOT).check_state():
            InstallLog(InstallState.MOVING_SNAPSHOT).add_state(InstallState.PENDING)

            print(Fore.YELLOW + "|----------[ Moving Snapshot to Node ]----------|")
            print(f"{Fore.RED}This will take a few minutes, please don't close your terminal session")
            subprocess_command(f"rm -r {cur_dir}/mainnet/geth")
            subprocess_command(f"mv -f {cur_dir}/server/data-seed/geth {cur_dir}/mainnet/")
            subprocess_command(f"rm -r {cur_dir}/server/")
            print("")

            InstallLog(InstallState.MOVING_SNAPSHOT).add_state(InstallState.DONE)

if not InstallLog(InstallState.CREATE_START_SH).check_state():
    InstallLog(InstallState.CREATE_START_SH).add_state(InstallState.PENDING)

    print(Fore.YELLOW + "|----------[ Creating Node Shell Script ]----------|")
    create_start_node()
    os.chmod("start.sh", permission)
    InstallLog(InstallState.CREATE_START_SH).add_state(InstallState.DONE)

if not InstallLog(InstallState.CREATE_NODE_SERVICE).check_state():
    InstallLog(InstallState.CREATE_NODE_SERVICE).add_state(InstallState.PENDING)

    print(Fore.YELLOW + "|----------[ Creating Node Service ]----------|")
    create_node_service()
    print(Fore.YELLOW + "|----------[ Starting Node Service ]----------|")
    subprocess_command("systemctl daemon-reload")
    subprocess_command("systemctl enable geth_bsc")
    subprocess_command("systemctl restart geth_bsc")
    InstallLog(InstallState.CREATE_NODE_SERVICE).add_state(InstallState.DONE)

if not InstallLog(InstallState.INSTALL_STATUS).check_state():
    print(Fore.GREEN + "================================")
    print(Fore.GREEN + "|    4. FINALIZE SETUP   |")
    print(Fore.GREEN + "================================")
    print("")
    InstallLog(InstallState.INSTALL_STATUS).add_state(InstallState.PENDING)

    print(Fore.YELLOW + "|----------[ Node Setup Done ]----------|")
    print(f"{Fore.WHITE}Deleting snapshot.tar.lz4")
    subprocess_command(f"rm -r snapshot.tar.lz4")

    print(f"{Fore.WHITE}Deleting mainnet.zip")
    subprocess_command(f"rm -r mainnet.zip")

    InstallLog(InstallState.INSTALL_STATUS).add_state(InstallState.DONE)

if not InstallLog(InstallState.CREATE_NODE_CONNECTION).check_state():
    InstallLog(InstallState.CREATE_NODE_CONNECTION).add_state(InstallState.PENDING)
    print(Fore.YELLOW + "|----------[ Creating Connection Command ]----------|")
    create_connection()
    print(f"{Fore.WHITE}Run this command to check your sync status:")
    print(f">>> {Fore.RED}node-sync")
    print(f"{Fore.WHITE}Run this command to check block left :")
    print(f">>> {Fore.RED}block-check")
    InstallLog(InstallState.CREATE_NODE_CONNECTION).add_state(InstallState.DONE)
