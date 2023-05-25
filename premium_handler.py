import json
import time
import subprocess, os
import requests

db = "anodevpn-server/clients.json"

def read_db():
    global db
    try:
        with open(db) as json_file:
            json_data = json.load(json_file)
            return json_data
    except FileNotFoundError:
        print(f"JSON file not found: {db}")
        exit(1)
        
def write_json(json_data):
    global db
    with open('w') as json_file:
        json.dump(json_data, json_file)
        
def insert_client(ip, address, start_time, end_time, paid, json_data):
    client = {
        "ip": ip,
        "address": address,
        "time": start_time,
        "paid": paid
    }
    json_data["clients"].append(client)
    return json_data

def retrieve_address(ip, json_data):
    for client in json_data["clients"]:
        if client["ip"] == ip:
            return client["address"]
    return None

def decimal_to_hex(decimal):
    return format(decimal, '02x')

def get_hex_from_ip(ip_address):
    # Extract the last two octets of the source IP address
    last_two_parts = ip_address.split('.')[-2:]

    part1 = last_two_parts[0]
    part2 = last_two_parts[1]

    # Convert each part to hexadecimal
    hex_part1 = decimal_to_hex(int(part1))
    hex_part2 = decimal_to_hex(int(part2))

    # Concatenate the hexadecimal parts
    hex_ip = hex_part1 + hex_part2

    return hex_ip

def addPremium(ip):
    print("Adding premium for {}".format(ip))
    lsLimitPaid = "950mbit"
    cmd = "tc class replace dev tun0 parent 1:fffe classid 1:{} hfsc ls m2 {} ul m2 {}".format(hex, lsLimitPaid, lsLimitPaid)
    subprocess.check_output(cmd, shell=True).decode('utf-8').rstrip()
    cmd = 'nft add element pfi m_client_leases { {} : "1:{}" }'.format(ip, hex)
    subprocess.check_output(cmd, shell=True).decode('utf-8').rstrip()
    
def removePremium(ip):
    print("Removing premium for {}".format(ip))
    lsLimitPaid = "950mbit"
    hex = get_hex_from_ip(ip)
    # Set required variables
    env = os.environ.copy()
    env[""]
    cmd = "tc class delete dev tun0 parent 1:fffe classid 1:{} hfsc ls m2 {} ul m2 {}".format(hex, lsLimitPaid, lsLimitPaid)
    subprocess.check_output(cmd, shell=True).decode('utf-8').rstrip()
    cmd = 'nft delete element pfi m_client_leases { {} : "1:{}" }'.format(ip, hex)
    subprocess.check_output(cmd, shell=True).decode('utf-8').rstrip()


def hasDurationEnded(start_time, duration):
    end_time = start_time + (duration*3600)
    current_time = time.time()
    if (current_time > end_time):
        return True
    else:
        return False

def getBalance(address):
    print("Getting balance for {}".format(address))
    # Get balance from the PKT blockchain
    url = "http://localhost:8080/api/v1/wallet/address/balances"
    response = requests.post(url, json={"showzerobalance": "false"}, headers={"Content-Type": "application/json"})
    if response.status_code == 200:
        balances = response.json()
        for address in balances["addrs"]:
            if address["address"] == address:
                return address["total"]
        return None
    else:
        print("Error getting response")
        return None
    
def isValidPayment(address, ip):
    premiumPrice = os.environ.get('PKTEER_PREMIUM_PRICE')
    # Check balance for the address
    balance = getBalance(address)
    if (balance is not None):
        if balance < premiumPrice:
            print("Client paid less than the premium price of {}: {}".format(premiumPrice, address["total"]))
            return False
        elif balance >= premiumPrice:
            print("Client paid the premium price of {}: {}".format(premiumPrice, address["total"]))
            return True
    else:
        print("Payment may not have come throught yet...")
        return False

                    
def main():
    waitingTime = 5 * 60 # 5 minutes
    # Read the clients.json file
    clients = read_db()
    for client in clients["clients"]:
        print(client)
        # Check the time for each client
        startTime = client["time"] / 1000 # convert to seconds
        if hasDurationEnded(startTime, client["duration"]):
            removePremium(client["ip"])
        currentTime = time.time()
        valid = isValidPayment(client["address"], client["ip"])
        if not valid and (startTime + waitingTime) < currentTime:
            print("Request came at {} but after waiting for {} the payment has not come through yet".format(startTime, waitingTime))
            removePremium(client["ip"])
        
    return
    
if __name__ == "__main__":
    main()