#!/bin/bash
# Script to run docker container
# and print out the VPN exit info

echo "Provide a name for your VPN Exit"
echo "VPN Name: "
read name
echo "Country of VPN Exit: "
read country
echo "Enter your pkt.chat username in order to get direct notifications about changes to your VPN Server:"
read username
valid_price=false
while [[ $valid_price == false ]]; do
    echo "Set price for Premium VPN in PKT (range of 1-100):"
    read price

    # Check if the input is NOT an integer or is not within the range of 1 to 100
    if [[ ! $price =~ ^[0-9]+$ ]] || [[ $price -lt 1 ]] || [[ $price -gt 100 ]]; then
        echo "Invalid input. The price should be an integer within the range of 1 to 100 PKT."
    else
        valid_price=true
    fi
done

IPERF_PORT=5201
echo "Running docker container PKT-Server..."
docker run -d --rm \
        --log-driver 'local' \
        --cap-add=NET_ADMIN \
        --device /dev/net/tun:/dev/net/tun \
        --sysctl net.ipv6.conf.all.disable_ipv6=0 \
        --sysctl net.ipv4.ip_forward=1 \
        -p $ANODE_SERVER_PORT:$ANODE_SERVER_PORT \
        -p $ANODE_SERVER_PORT:$ANODE_SERVER_PORT/udp \
        -p $IPERF_PORT:$IPERF_PORT \
        -p $IPERF_PORT:$IPERF_PORT/udp \
        -e "PKTEER_NAME=$name" \
        -e "PKTEER_COUNTRY=$country" \
        -e "PKTEER_CHAT_USERNAME=$username" \
        -e "PKTEER_PREMIUM_PRICE=$price" \
        --name pkt-server pkt-server

# Launch PKT Wallet
echo "Starting PKT Wallet..."
docker exec pkt-server /server/pktd/bin/pld > /dev/null 2>&1 &
sleep 1
docker exec pkt-server /server/create_wallet.sh
echo "After saving your seed, press any key to continue..."
read -n 1 -s
docker exec pkt-server /server/init.sh
docker exec pkt-server /server/vpn_info.sh
docker exec pkt-server python3 /server/premium_handler.py &
docker exec pkt-server /server/run_iperf3.sh &
docker exec pkt-server /server/kill_iperf3.sh &
