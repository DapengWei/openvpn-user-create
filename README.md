
# A tutorial for building a certificate authentication  OpenVPN server with packet filter

----------

## Install  OpenVPN

Server: Ubuntu 20.04 LTS

Install packages:

```shell
apt install openvpn unzip gcc easy-rsa build-essential
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

### Build minimal pf

minimal\_pf.c:

```c
/* minimal_pf.c 
 * ultra-minimal OpenVPN plugin to enable internal packet filter */
#include <stdio.h>
#include <stdlib.h>

#include "include/openvpn-plugin.h"

/* dummy context, as we need no state */
struct plugin_context {
  int dummy;
};

/* Initialization function */
OPENVPN_EXPORT openvpn_plugin_handle_t openvpn_plugin_open_v1 (unsigned int *type_mask, const char *argv[], const char *envp[]) {
  struct plugin_context *context;
  /* Allocate our context */
  context = (struct plugin_context *) calloc (1, sizeof (struct plugin_context));

  /* Which callbacks to intercept. */
  *type_mask = OPENVPN_PLUGIN_MASK (OPENVPN_PLUGIN_ENABLE_PF);

  return (openvpn_plugin_handle_t) context;
}

/* Worker function */
OPENVPN_EXPORT int openvpn_plugin_func_v2 (openvpn_plugin_handle_t handle,
            const int type,
            const char *argv[],
            const char *envp[],
            void *per_client_context,
            struct openvpn_plugin_string_list **return_list) {
  
  if (type == OPENVPN_PLUGIN_ENABLE_PF) {
    return OPENVPN_PLUGIN_FUNC_SUCCESS;
  } else {
    /* should not happen! */
    return OPENVPN_PLUGIN_FUNC_ERROR;
  }
}

/* Cleanup function */
OPENVPN_EXPORT void openvpn_plugin_close_v1 (openvpn_plugin_handle_t handle) {
  struct plugin_context *context = (struct plugin_context *) handle;
  free (context);
}
```

Prepare build script:

build.sh:

```shell
INCLUDE="-I/usr/local/src/openvpn-2.3.11"         # CHANGE THIS!!!!
CC_FLAGS="-O2 -Wall -g"
NAME=minimal_pf
gcc $CC_FLAGS -fPIC -c $INCLUDE $NAME.c && \
gcc $CC_FLAGS -fPIC -shared -Wl,-soname,$NAME.so -o $NAME.so $NAME.o -lc
```

compile and install:

```shell
bash ./build.sh
cp minimal_pf.so /etc/openvpn
```

### Create client-connect.sh script

```shell
cd /etc/openvpn
touch client-connect.sh
```

client-connect.sh:

```shell
#!/bin/sh

# /etc/openvpn/client-connect.sh: sample client-connect script using pf rule files

# rules template file
template="/etc/openvpn/rules/${common_name}.pf"

# create the file OpenVPN wants with the rules for this client
if [ -f "$template" ] && [ ! -z "$pf_file" ]; then
  cp -- "$template" "$pf_file"
else
  # if anything is not as expected, fail
  exit 1
fi
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
mkdir {ccd,rules,logs}
touch /etc/openvpn/logs/openvpn-status.log
touch /etc/openvpn/logs/openvpn.log
```

### Create Server configuration

wdphomevpn.conf:

```shell
port 1199
proto tcp
dev tun
ca /etc/openvpn/easy-rsa/pki/ca.crt
cert /etc/openvpn/easy-rsa/pki/issued/wdphomevpn.crt
key /etc/openvpn/easy-rsa/pki/private/wdphomevpn.key
dh /etc/openvpn/easy-rsa/pki/dh.pem
server 10.240.0.0 255.255.255.0
ifconfig-pool-persist  /etc/openvpn/ipp.txt
client-config-dir  /etc/openvpn/ccd

#If you revoke some user certificate, uncomment this
;crl-verify /etc/openvpn/easy-rsa/pki/revoked/certs_by_serial/crl.pem

keepalive 10 120
compress lzo
persist-key
persist-tun
push "route 10.240.0.0 255.255.255.0"

cipher AES-256-GCM
auth SHA512
tls-version-min 1.2
tls-cipher TLS-DHE-RSA-WITH-AES-256-GCM-SHA384

status /etc/openvpn/logs/openvpn-status.log
log-append  /etc/openvpn/logs/openvpn.log

verb 3

#configuration for minimal pf
plugin /etc/openvpn/minimal_pf.so
client-connect /etc/openvpn/client-connect.sh
script-security 3
```

## Create minimal pf rule for user

```shell
cd /etc/openvpn/rules
```

Use the same name for rule file and vpn name.

```shell
touch wdphomevpn-dapeng-internal.pf
```

format below:

```shell
[CLIENTS ACCEPT]
[SUBNETS DROP]
+10.241.12.2/32
[END]
```

ACCEPT or DROP is the default policy, control the user can connect other clients or subnets.
Then you can add other rules for allow list(+) or deny list(-).

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
dev tun-home
proto tcp
remote <serverip> 1199
resolv-retry infinite
nobind
persist-key
persist-tun
compress lzo

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
python create_openvpn.py -n name -d {user rule group name}
```

Create user group rule template in `./template`

Auto created user configuration in `./ovpn`

Change client configuration template in `client.tp`

## Revoke user certificate

```shell
cd /usr/share/easy-rsa

source ./vars

./revoke-full ksc-name
```