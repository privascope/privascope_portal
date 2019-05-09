#! /bin/ash
set -e

# Set up certificates and args if using TLS
if [ $DOCKER_TLS_VERIFY -eq 1 ]; then
    echo Writing certificates...
    # Client certs, since we have to run 'docker' from here for network setup
    mkdir -pv ~/.docker
    echo -e "$DOCKER_TLSCACERT" > ~/.docker/ca.pem
    echo -e "$DOCKER_CLIENT_TLSCERT" > ~/.docker/cert.pem
    echo -e "$DOCKER_CLIENT_TLSKEY" > ~/.docker/key.pem
    # Server certs
    echo -e "$DOCKER_TLSCACERT" > ca.pem
    echo -e "$DOCKER_SERVER_TLSCERT" > server-cert.pem
    echo -e "$DOCKER_SERVER_TLSKEY" > server-key.pem
    ARGS="--tlsverify --tlscacert=ca.pem --tlscert=server-cert.pem --tlskey=server-key.pem"
fi
# Start up dockerd in the background so we can do a few more things
sh /usr/local/bin/dockerd-entrypoint.sh $ARGS &
PID=$!

# Wait to make sure it started
sleep 5

# Set up job-network with resource whitelist.
NETWORK_ID=$(docker network create job-network)
NETWORK_ID_SHORT=$(echo $NETWORK_ID | head -c 12)
NETWORK_INTERFACE_PREFIX=br-
NETWORK_INTERFACE=$NETWORK_INTERFACE_PREFIX$NETWORK_ID_SHORT

echo $(iptables -L -v -n)

iptables -I DOCKER-USER -i $NETWORK_INTERFACE -j DROP

echo $JOB_RESOURCES
iptables -I DOCKER-USER -i $NETWORK_INTERFACE -d $JOB_RESOURCES -j ACCEPT

echo $(iptables -L -v -n)

wait $PID
