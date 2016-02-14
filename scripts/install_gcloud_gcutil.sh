#!/bin/bash

apt-get install -y curl --no-install-recommends
curl https://sdk.cloud.google.com | bash
gcloud auth login
gcloud config set 'cppr-bench'
