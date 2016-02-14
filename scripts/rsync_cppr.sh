#!/bin/bash

rsync -avz --stats --progress \
~/cppr/src/ theo@$VPS:/home/theo/cppr_sync/ \
--filter='- .Sync*'  \
--filter='- gathered_data/*' \
--filter='- *.pyc'
