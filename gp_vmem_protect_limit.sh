#!/bin/bash

#!/bin/bash

set -e

# Check arg count
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <VCPU_COUNT> <OTHER_MEMORY_MB>"
    exit 1
fi

RAM=`free -m | perl -l -ne '/Mem:\s+(\d+)/ && print $1'`
SWAP=`free -m | perl -l -ne '/Swap:\s+(\d+)/ && print $1'`

NumOfSegs=$1
GPDBOtherMem=$2

# How much of the swap space are we willing to add to the GP
# vmem. 0.5 allows half of the swap space
SWAP_FACTOR=0.5


echo `perl -e  "print(int((($SWAP_FACTOR * $SWAP)  + ($RAM - $GPDBOtherMem)) / $NumOfSegs))"`

