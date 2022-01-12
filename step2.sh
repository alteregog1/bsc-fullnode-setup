#!/bin/sh

echo "========================================================="
echo "=    Extracting Snapshot                                ="
echo "========================================================="
lz4 -d geth.tar.lz4 | tar -xv
rm -r geth.tar.lz4
echo "========================================================="
echo "=   Moving Snapshot to Node                             ="
echo "========================================================="
rm -r ${PWD}/node/geth
mv -f ${PWD}/server/data-seed/geth ${PWD}/node/
rm -r ${PWD}/server/
