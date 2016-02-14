#!/bin/bash

# To be run inside a Ubuntu 14.04 docker

sudo apt-get install -y g++ python2.7-dev libboost-all-dev libexpat1-dev libcgal-dev libcairomm-1.0-dev python-cairo python-matplotlib
sudo apt-get install -y git-core automake libtool python-scipy python-numpy python-cairo-dev wget vim

wget -O libsparsehash2.deb 'https://sparsehash.googlecode.com/files/sparsehash_2.0.2-1_amd64.deb'
sudo dpkg -i libsparsehash2.deb

./autogen.sh
./configure --enable-openmp
# Note: -j4 is the limit if you have about 10-12G of free RAM, even with this it will swap
# at the end
time make -j4
sudo make install
