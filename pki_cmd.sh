cd $1
source ./vars
./easyrsa gen-req $2 nopass
./easyrsa sign-req client $2
