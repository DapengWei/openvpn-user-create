#!/bin/bash

cd $1
./easyrsa build-client-full $2 nopass

