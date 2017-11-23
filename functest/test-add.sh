#!/bin/bash

set -e

source common.sh

dvc_create_repo

dvc_info "Add file"
cp $DATA_CACHE/foo data/local
dvc add data/local
dvc_check_files "data/local .dvc/state/data/local.state .dvc/state/data/local.cache_state"
dvc_pass
