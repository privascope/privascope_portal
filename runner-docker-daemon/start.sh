#! /bin/ash
set -e

sh /usr/local/bin/dockerd-entrypoint.sh &
PID=$!

sleep 5

NETWORK_ID=$(docker network create job-network)
NETWORK_ID_SHORT=$(echo $NETWORK_ID | head -c 12)
NETWORK_INTERFACE_PREFIX=br-
NETWORK_INTERFACE=$NETWORK_INTERFACE_PREFIX$NETWORK_ID_SHORT

echo $(iptables -L -v -n)

iptables -I DOCKER-USER -i $NETWORK_INTERFACE -j DROP

echo $JOB_RESOURCES
while [ "$JOB_RESOURCES" ]; do
    i=${JOB_RESOURCES%%;*}
    echo $i
    iptables -I DOCKER-USER -i $NETWORK_INTERFACE -d $i -j ACCEPT
    [ "$JOB_RESOURCES" = "$i" ] && \
        JOB_RESOURCES='' || \
        JOB_RESOURCES="${JOB_RESOURCES#*;}"
done

echo $(iptables -L -v -n)

wait $PID
