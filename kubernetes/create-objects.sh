#!/bin/bash
set -eu

objects=(
  "db-deployment" \
  "db-persistentvolumeclaim" \
  "db-service" \
  "job-files-persistentvolumeclaim" \
  "portal-deployment" \
  "portal-route" \
  "portal-service" \
  "rabbit-deployment" \
  "rabbit-persistentvolumeclaim" \
  "rabbit-service" \
  "runner-worker-deployment" \
  "runner-worker-service"
)

echo "Exporting variables from: $1"
source $1
mkdir ./output

for obj in ${objects[@]}; do
  echo "Substituting variables for $obj"
  envsubst < "./$obj.sample.yaml" > "./output/$obj.yaml"
done

echo "Done"
