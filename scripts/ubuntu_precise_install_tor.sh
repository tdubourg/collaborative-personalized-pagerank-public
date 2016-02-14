#!/bin/bash

sudo su -c 'echo  "deb     http://deb.torproject.org/torproject.org precise main" >> /etc/apt/sources.list'
sudo gpg --keyserver keys.gnupg.net --recv 886DDD89
sudo gpg --export A3C4F0F979CAA22CDBA8F512EE8CBC9E886DDD89 | sudo apt-key add -
sudo apt-get update
sudo apt-get install deb.torproject.org-keyring tor --no-install-recommends
service tor restart

sudo apt-get install privoxy --no-install-recommends
sudo su -c 'echo "forward-socks5 / 127.0.0.1:9050 ." >> /etc/privoxy/config'
sudo su -c 'echo "forward-socks4a / 127.0.0.1:9050 ." >> /etc/privoxy/config'
sudo su -c 'echo "listen-address 127.0.0.1:8118" >> /etc/privoxy/config'
# forward-socks4a / 127.0.0.1:9050 .

#restart it 
service privoxy restart
netstat -anpe | grep -i --color=auto privoxy
netstat -anpe | grep -i --color=auto 8118
netstat -anpe | grep -i --color=auto 9050
