#!/bin/bash

cd $1
./easyrsa --batch build-client-full $2 nopass

