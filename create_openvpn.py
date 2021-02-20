#!/usr/bin/env python
import os
import re
import sys
import getopt
import subprocess

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
OVPN_TP = os.path.join(CURRENT_DIR, "client.tp")
KEYTOOL_DIR = "/etc/openvpn/easy-rsa/"
KEY_DIR = os.path.join(KEYTOOL_DIR, "pki")
OVPNCFG_DIR = os.path.join(CURRENT_DIR, "ovpn")
PFTP_DIR = os.path.join(CURRENT_DIR, "template")
PF_DIR = "/etc/openvpn/rules"
NAME_PREFIX = ""
PF_FILE = os.path.join(CURRENT_DIR, "ovpn_pf.csv")


def create_key(user_name):
    pki_cmd = "bash -c " + "'" + os.path.join(CURRENT_DIR, "pki_cmd.sh") + " " + KEYTOOL_DIR + " " + user_name + "'"
    print(pki_cmd)
    subprocess.call(pki_cmd, shell=True)


def create_conf(user_name):
    with open(os.path.join(OVPNCFG_DIR, user_name + ".ovpn"), "w") as cfg_file:
        for line in open(OVPN_TP):
            cfg_file.write(line)

        cfg_file.write("\n" + "<cert>" + "\n")
        user_crt = os.path.join(KEY_DIR, "issued", user_name + ".crt")
        write_flag = 0
        for line in open(user_crt):
            if re.match("-----BEGIN CERTIFICATE-----", line):
                write_flag = 1
            if write_flag == 1:
                cfg_file.write(line)
        cfg_file.write("</cert>" + "\n")

        cfg_file.write("<key>" + "\n")
        user_key = os.path.join(KEY_DIR, "private", user_name + ".key")
        write_flag = 0
        for line in open(user_key):
            if re.match("-----BEGIN PRIVATE KEY-----", line):
                write_flag = 1
            if write_flag == 1:
                cfg_file.write(line)
        cfg_file.write("</key>" + "\n")

        cfg_file.write("<ca>" + "\n")
        ca_file = os.path.join(KEY_DIR, "ca.crt")
        write_flag = 0
        for line in open(ca_file):
            if re.match("-----BEGIN CERTIFICATE-----", line):
                write_flag = 1
            if write_flag == 1:
                cfg_file.write(line)
        cfg_file.write("</ca>" + "\n")

def create_pf(user_name, user_dept):
    create_pf_cmd = "cp -r " + os.path.join(PFTP_DIR, user_dept + ".pf") + " " + os.path.join(PF_DIR, user_name + ".pf")
    print(create_pf_cmd)
    subprocess.call(create_pf_cmd, shell=True)
    with open(PF_FILE, "a") as ovpn_file:
        write_cache = user_name + "," + user_dept + "\n"
        ovpn_file.write(write_cache)


def main():
    opts, args = getopt.getopt(sys.argv[1:], "n:d:h")

    pftp_dirs = os.walk(PFTP_DIR)
    for root, dirs, files in pftp_dirs:
        pftp_list = [i.split(".")[0] for i in files]

    for op, value in opts:
        if op == "-n":
            user_name = NAME_PREFIX + value
        if op == "-d":
            if value in pftp_list:
                user_dept = value
            else:
                print("group error:",end='')
                for i in pftp_list:
                    print(i + ',',end='')
                print("")
                sys.exit()
        if op == "-h":
            print("create_openvpn.py -n <name> -d <group>")
            sys.exit()

    create_key(user_name)
    print("create user private key finished!")

    create_conf(user_name)
    print("create user cfg file finished!")

    create_pf(user_name, user_dept)
    print("create pf cfg file finished!")

if __name__ == "__main__":
    main()
