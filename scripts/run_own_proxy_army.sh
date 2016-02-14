#!/bin/bash

n=6
start=42
for i in `seq $start \`expr $start + $n - 1\``; do \
  gcutil --service_version="v1" --project="cppr-bench" adddisk "instance-${i}" --zone="europe-west1-b" --source_snapshot="cppr-small2-snapshot1" --disk_type="pd-standard"; \
  gcutil --service_version="v1" --project="cppr-bench" addinstance "instance-${i}" --zone="europe-west1-b" --machine_type="f1-micro" --network="default" --external_ip_address="ephemeral" --metadata="sshKeys:root:ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDZfOoI0tdk06ll9wK4yuTPauLpn4UIKQlNu7K/+81lB6EgnUUQ9pzrAWiJd1TZ708SmvakWfV5f+8PwoKjHzTdcuAqJ/mWgGE4yS6jCQQP/TGfRUdesDJhiAorjNfNSa/qpHPFCjRqQNBq4JQpg1Uq0HX/CIszKNwK6jJz+r9bCyrbZSS7pvc4ULjiSjLqN9JYqH7UxBkX04rGo6VdgGj4W/LIO0KkNH0t76K5hnXM55qRplFR4UoOBZ2qsx5vYlU1HO1Jb9f/I/p7txL8ryvvP6ACMbplm0ZQIejFIFKlYZdcZZ4MBClL4St+eoCnFC3w1L5e7N5Ca8+ZWWe/9Flj root@16501fc5eaac\u000atroll:ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDChHUSzMIsgu7QFNm7OJA3oqatIyLD1fwwx/I3WCuJ9DgGD/tLOYOT3SdeW6eannTXWu4XVrFjDoXwllbFxuRiLmmGUhBDrOKSpcNl70q/0O8o6qUdi6/A8PLSD4cekZysJnD+hcWXKKYtT/Jj65zJ7GNkFxg5hQx8n45c053syZErl4PKygwk+IOshCZHRYz/JF3a5D7ZjyaiatUljTtqlFBuQ60TW2BQ7b7P2GAPha/QEA+Mwn60cn4Sj+O/Dz0iFLbxImEZ4Q5xA2ztLTM0SI4fyewaA4mg2IZtDHLcZlj9LXkVwgRjMNHs80XxlzboCmbhF0Ens/eWjUnfPCY5 troll@troll-fedora" --can_ip_forward="true" --tags="http-server,https-server" --disk="instance-${i},deviceName=instance-${i},mode=READ_WRITE,boot" --auto_delete_boot_disk="true"; \
done

ips=`gcutil --project='cppr-bench' listinstances --format csv --columns 'external-ip' 2>/dev/null | tail -n+2`

echo "Killing all SSH and privoxy instances."
kill -TERM `pidof ssh`
service privoxy stop
kill -TERM `pidof privoxy`
echo "Restarting the default privoxy service..."
service privoxy start

port_ssh=1235
port_privoxy=8120
proxy_list=''
for i in $ips; do \
  echo $i; \
  port_ssh=`expr $port_ssh + 1`; \
  port_privoxy=`expr $port_privoxy + 1`; \
  proxy_list="${proxy_list} 127.0.0.1:${port_privoxy}"; \
  echo "SSH connection on $port_ssh..."; \
  ssh -f -N -D "127.0.0.1:$port_ssh" -oStrictHostKeyChecking=no $i; \
  echo "Done"; \
  conf=/etc/privoxy/config$i; \
  echo "Privoxy conf file=${conf} with port=$port_privoxy"; \
  echo "forward-socks5 / 127.0.0.1:$port_ssh ." > $conf; \
  echo "forward-socks4a / 127.0.0.1:$port_ssh ." >> $conf; \
  echo "listen-address 127.0.0.1:$port_privoxy" >> $conf; \
  privoxy $conf; \
  echo "Done ${i}"; \
done

echo "Proxies IPs are:"
echo "["
for i in $proxy_list; do echo "    '"$i"',"; done
echo "]"