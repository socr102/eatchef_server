#!/bin/bash
set -e
echo "$DOCKER_HUB_PASSWORD" | docker login --username $DOCKER_HUB_USERNAME --password-stdin
export BITBUCKET_USERNAME=$PIPE_BITBUCKET_USERNAME
export BITBUCKET_PASSWORD=$PIPE_BITBUCKET_PASSWORD
export MAIN_IMAGE=$MAIN_IMAGE
export MAIN_DIR="server"
export REPO_URL=""
if [ -d "$MAIN_DIR" ]; then rm -rf $MAIN_DIR; fi
git clone --single-branch --branch master "$REPO_URL" $MAIN_DIR

cd $MAIN_DIR/ci/production/

python3 scripts.py create_env
python3 scripts.py load_env
python3 scripts.py pull_main
python3 scripts.py up_postgre_rabbit
python3 scripts.py stop_main_api
python3 scripts.py stop_main_tasks
python3 scripts.py stop_main_beat
python3 scripts.py up_main_api true true
python3 scripts.py up_main_tasks
python3 scripts.py up_main_beat

cd ~ && rm -rf $MAIN_DIR

exec "$@"
