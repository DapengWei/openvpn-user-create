
# A tutorial for building a certificate authentication  OpenVPN server and creating user profile
----------

## Install  OpenVPN

Server: Ubuntu 20.04 LTS

Install packages:

```shell
apt install openvpn easy-rsa build-essential
```

## Install packge filter module

Reference link: <http://backreference.org/2010/06/18/openvpns-built-in-packet-filter/>

### Download  OpenVPN source code

``` shell
apt install libssl-dev liblzo2-dev libpam0g-dev autoconf libtool automake
cd /usr/local/src/
wget https://swupdate.openvpn.org/community/releases/openvpn-2.3.11.zip # change this for your openvpn version
cd openvpn-2.3.11/
touch minimal_pf.c
autoreconf -vi
./configure
```
## Create server certificate

### install easy-rsa

```shell
ln -s /usr/share/easy-rsa/ /etc/openvpn/easy-rsa
```

### Prepare env vars file

```shell
cd /etc/openvpn/easy-rsa/
cp vars.example vars
```

add below to vars:

```shell
set_var EASYRSA_DN "org"
set_var EASYRSA_REQ_COUNTRY "CN"
set_var EASYRSA_REQ_PROVINCE "Beijing"
set_var EASYRSA_REQ_CITY "Beijing"
set_var EASYRSA_REQ_ORG "unknown"
set_var EASYRSA_REQ_EMAIL "unknown@mail.com"
set_var EASYRSA_REQ_OU  "unknown"
```

### Create certificate

CA

```shell
./easyrsa init-pki
./easyrsa build-ca nopass
./easyrsa gen-dh
```

Server

```shell
./easyrsa build-server-full wdphomevpn nopass
```

User

```shell
./easyrsa build-client-full wdphomevpn-dapeng-internal nopass
```

## Create OpenVPN Server configuration

### Create dir

```shell
cd /etc/openvpn
mkdir {ccd,logs}
touch /etc/openvpn/logs/openvpn-status.log
touch /etc/openvpn/logs/openvpn.log
```

### Create Server configuration

/etc/openvpn/server/wdphomevpn.conf:

```shell
port 1199
proto tcp
dev tun
ca /etc/openvpn/easy-rsa/pki/ca.crt
cert /etc/openvpn/easy-rsa/pki/issued/wdphomevpn.crt
key /etc/openvpn/easy-rsa/pki/private/wdphomevpn.key
dh /etc/openvpn/easy-rsa/pki/dh.pem
server 10.242.0.0 255.255.255.0
topology subnet
ifconfig-pool-persist  /etc/openvpn/ipp.txt
client-config-dir  /etc/openvpn/ccd

# If you revoke some user certificate, uncomment this
;crl-verify /etc/openvpn/easy-rsa/pki/revoked/certs_by_serial/crl.pem

keepalive 10 120
persist-key
persist-tun

# One cert can be used by more than one connection/users.
duplicate-cn

client-to-client
# Add your route here, uncomment
;push "route 10.241.0.0 255.255.0.0"

cipher AES-256-GCM
auth SHA512
tls-version-min 1.2
tls-cipher TLS-DHE-RSA-WITH-AES-256-GCM-SHA384

status /etc/openvpn/logs/openvpn-status.log
log-append  /etc/openvpn/logs/openvpn.log

verb 3
```

## add iptables NAT rule

```shell
iptables -A FORWARD -s 10.240.0.0/24  -j ACCEPT
iptables -t nat -A POSTROUTING -s 10.240.0.0/24 -o eth0 -j MASQUERADE # change this for your NIC and your OpenVPN subnet
```

## Start the server

```shell
systemctl start openvpn-server@wdphomevpn.service
```

## Client configuration

wdphomevpn-dapeng-internal.ovpn:

```shell
client
dev tun-client
proto tcp
remote <serverip> 1199
resolv-retry infinite
nobind
persist-key
persist-tun

cipher AES-256-GCM
auth SHA512
tls-version-min 1.2
tls-cipher TLS-DHE-RSA-WITH-AES-256-GCM-SHA384

mssfix 1400
verb 3
<cert>
add cert here
</cert>
<key>
add private key here
</key>
<ca>
add ca here
</ca>
```

## Script for create user

clone this project in to `/etc/openvpn/`

```shell
python create_openvpn.py -n name
```

Auto created user configuration in `./ovpn`

Change client configuration template in `client.tp`

## Revoke user certificate

```shell
cd /usr/share/easy-rsa

source ./vars

./revoke-full name
```