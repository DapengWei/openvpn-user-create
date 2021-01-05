#!/usr/bin/env python
import os
import sys
import subprocess


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PFTP_DIR = os.path.join(CURRENT_DIR, "template")
PF_DIR = "/etc/openvpn/rules"
PF_LIST = os.path.join(CURRENT_DIR, "ovpn_pf.csv")


def read_list(pf_file):
    pf_list = []
    with file(pf_file) as pf_file_handle:
        for line in pf_file_handle:
            pf_list.append(line.strip("\n").split(","))
    return pf_list


def create_pf(user_name, user_dept):
    create_pf_cmd = "cp -r " + os.path.join(PFTP_DIR, user_dept + ".pf") + " " + os.path.join(PF_DIR, user_name + ".pf")
    print create_pf_cmd
    subprocess.call(create_pf_cmd, shell=True)


def main():
    pf_list = read_list(PF_LIST)
    print pf_list
    for i in pf_list:
        create_pf(i[0], i[1])

if __name__ == "__main__":
    main()
