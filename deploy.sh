#!/bin/bash
set -e

if [ -z "$DEPLOY_USER" ]; then echo "DEPLOY_USER environment variable is not set!"; exit 1; fi
if [ -z "$DEPLOY_PATH" ]; then echo "DEPLOY_PATH environment variable is not set!"; exit 1; fi
if [ -z "$DEPLOY_PASS" ]; then echo "DEPLOY_PASS environment variable is not set!"; exit 1; fi

# Upload the RPM to the RPM repository
# by exportin it to SSHPASS, sshpass wont log the command line and the password
export SSHPASS=$DEPLOY_PASS
sshpass -e scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -r /tmp/gp-rpm-build/_build/x86_64/* $DEPLOY_USER@$DEPLOY_HOST:$DEPLOY_PATH

# Update the RPM repository
export DEPLOY_CMD="createrepo ${DEPLOY_PATH}/"
sshpass -e ssh  -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no $DEPLOY_USER@$DEPLOY_HOST $DEPLOY_CMD
