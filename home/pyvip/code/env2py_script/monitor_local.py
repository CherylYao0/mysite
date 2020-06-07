#!/usr/bin/env python2.7
# encoding:utf8

from __future__ import division
import os, json, commands, linecache, time, re, sys, subprocess
from decimal import Decimal
from Publiclass import Command
from collections import Counter

reload(sys)
sys.setdefaultencoding('utf8')


def check_snmp_net():
    statlist = {}
    stat = {}
    try:
        for i in linecache.getlines('/proc/net/dev'):
            line = i.replace(':', ' ').replace('|', '')
            if 'eth' in line or 'em' in line:
                stat['ethRBytes'] = line.split()[1]
                stat['ethRPackets'] = line.split()[2]
                stat['ethRErrs'] = line.split()[3]
                stat['ethRDrop'] = line.split()[4]
                stat['ethTBytes'] = line.split()[9]
                stat['ethTPackets'] = line.split()[10]
                stat['ethTErrs'] = line.split()[11]
                stat['ethTDrop'] = line.split()[12]
        statlist['status'] = stat
        linecache.clearcache()
    except ValueError:
        statlist['status'] = 1
    return statlist


###系統狀態####

# 主機負載#
def check_load():
    statlist = {}
    stat = {}
    try:
        loadavg = linecache.getlines('/proc/loadavg')
        stat['load_15'] = loadavg[0].split()[2]
        stat['load_5'] = loadavg[0].split()[1]
        stat['load_1'] = loadavg[0].split()[0]
        statlist['status'] = stat
    except ValueError:
        statlist['status'] = 1
    return statlist


# CPU使用率#
def check_cpu():
    statlist = {}
    stat = {}
    try:
        result = commands.getoutput('grep -c "model name" /proc/cpuinfo')
        stat['cpu_count'] = int(result)
        line = os.popen('top -bi -n 2 -d 0.02').read().split('\n\n\n')[1].split('\n')[2].split(':')[1].strip()
        line_l = [round(Decimal(i.strip().split('%')[0]), 2) for i in line.split(',')]
        stat['cpu_us'] = line_l[0]
        stat['cpu_sys'] = line_l[1]
        stat['cpu_ni'] = line_l[2]
        stat['cpu_idle'] = line_l[3]
        stat['cpu_wa'] = line_l[4]
        stat['cpu_hi'] = line_l[5]  # 硬中断（Hardware IRQ）占用CPU的百分比
        stat['cpu_si'] = line_l[6]  # 软中断（Software Interrupts）占用CPU的百分比
    except:
        stat = {}
    statlist['status'] = stat
    return statlist


# 主機內存#
def check_mem():
    statlist = {}
    stat = {}
    try:
        data = commands.getoutput('cat /proc/meminfo').split('\n')
        dev = {}
        for i in data:
            dev[i.split(':')[0]] = int(i.split()[1])
        physical_percent = round(
            Decimal(dev['MemTotal'] - dev['MemFree'] - dev['Buffers'] - dev['Cached']) / Decimal(dev['MemTotal']) * 100,
            2)
        stat['physical_percent'] = physical_percent
        if dev['SwapTotal'] > 0:
            virtual_percent = round(Decimal(dev['SwapTotal'] - dev['SwapFree']) / Decimal(dev['SwapTotal']) * 100, 2)
            stat['virtual_percent'] = virtual_percent
        else:
            stat['virtual_percent'] = '0.00%'
        statlist['status'] = stat
    except ValueError:
        statlist['status'] = 1
    return statlist


'''虛擬內存,缓冲内存 slab,高速缓存'''


# 磁盤容量#
def check_storage():
    statlist = {}
    stat = {}
    try:
        # 磁盘使用百分比
        line = commands.getoutput('/bin/df -h').split('\n')
        disk_list = [disk for disk in line]
        del (disk_list[0])
        if len(disk_list[0].split()) == 1:
            # 可能存在 /dev/mapper/VolGroup-lv_root （逻辑卷）独占一行的情况
            disk_info = disk_list[2:]
            disk_info.insert(0, disk_list[0] + disk_list[1])
        else:
            disk_info = disk_list
        for disk in disk_info:
            stat[disk.split()[0]] = disk.split()[-2]
        statlist['status'] = stat
        # 磁盘inode使用百分比
        line_i = commands.getoutput('/bin/df -i').split('\n')
        inode_list = [l for l in line_i]
        del (inode_list[0])
        if len(inode_list[0].split()) == 1:
            # 可能存在 /dev/mapper/VolGroup-lv_root （逻辑卷）独占一行的情况
            inode_info = inode_list[2:]
            inode_info.insert(0, inode_list[0] + inode_list[1])
        else:
            inode_info = inode_list
        for i in inode_info:
            stat[i.split()[0] + '_inode'] = i.split()[-2]
        statlist['status'] = stat
    except ValueError:
        statlist['status'] = 1
    return statlist


# 磁盤io#
def check_io():
    statlist = {}
    stat = {}
    if not os.path.exists('/usr/bin/iostat'):
        os.system("yum -y install sysstat >> /dev/null")
    try:
        line = commands.getoutput('sudo /sbin/fdisk -l | /bin/grep "Disk" | grep -v "identifier"').split('\n')
        disklist = [i for i in line]
        disk_t = [i.split()[1].split(':')[0].split('/')[-1] for i in disklist]
        io_info = {}
        for disk in disk_t:
            stat_t = commands.getoutput('/usr/bin/iostat -x -k -d %s' % disk).split('\n')[-2].split()
            if stat_t[0] == disk:
                io_info['r_count'] = stat_t[3]
                io_info['w_count'] = stat_t[4]
                io_info['r_rate'] = stat_t[5]
                io_info['w_rate'] = stat_t[6]
                io_info['util'] = stat_t[-1]
                stat[disk] = io_info
        statlist['status'] = stat
    except ValueError:
        statlist['status'] = 1
    return statlist


# 系統進程#
def check_sys_process():
    statlist = {}
    stat = {}
    try:
        sys_process = commands.getoutput("/bin/ps -el|grep -v grep |sed -n '2,$p'|awk '{print $2}'").split('\n')
        result = Counter(sys_process)
        stat['total_process'] = len(sys_process)
        stat['run_process'] = result['R']  # 运行
        stat['unsleep_process'] = result['D']  # 不可中断  uninterruptible sleep
        stat['sleep_process'] = result['S']  # 中断 sleeping
        stat['zombie_process'] = result['Z']  # 僵尸
        stat['stopped_process'] = result['T']  # 停止 traced or stopped
        statlist['status'] = stat
    except ValueError:
        statlist['status'] = 1
    return statlist


# 登錄用戶數#
def check_login_user():
    statlist = {}
    stat = {}
    try:
        login_user = commands.getoutput("/usr/bin/who | /usr/bin/wc -l").split('\n')
        stat['login_user'] = login_user[0]
        statlist['status'] = stat
    except ValueError:
        statlist['status'] = 1
    return statlist


# 運行時間 （以秒为单位）
def check_uptime():
    statlist = {}
    stat = {}
    try:
        uptime = linecache.getline('/proc/uptime', 1).split()[0]
        stat['uptime'] = uptime
        statlist['status'] = stat
    except ValueError:
        statlist['status'] = 1
    return statlist


def max_process():
    tmp = {}
    valuetmp = {}
    slist = ''
    if os.path.exists("/usr/sbin/lsof"):
        pass
    else:
        os.system("yum -y install lsof")
    count = commands.getoutput("/usr/sbin/lsof -n | sed '1d' | awk '{print $2}'")
    for pid in count.split('\n'):
        if pid in tmp.keys():
            tmp[pid] += 1
        else:
            tmp[pid] = 1
    data = sorted(tmp.items(), key=lambda tmp: tmp[1])
    for row in data[-1:]:
        result = row[0]
        out = commands.getoutput("/bin/ps aux | awk '$2 == %s {print $11}'" % result)
        if out.split('\n')[0] in valuetmp.keys():
            pass
        else:
            valuetmp[out.split('\n')[0]] = row[1]
            slist = str(out.split('\n')[0]) + ':' + str(row[1])
    return slist


def check_ulimit():
    statlist = {}
    stat = {}
    try:
        slist = max_process()
        file_handle = slist[-1].split(':')[-1]
        # 文件句柄
        all_handle = commands.getstatusoutput("/usr/sbin/lsof -n | sed '1d' | wc -l")[1]
        max_handle = commands.getstatusoutput('ulimit -n')[1]
        pervalue = int(file_handle) * 100 / int(max_handle)
        stat['max_handle'] = max_handle
        stat['all_handle'] = all_handle
        stat['pervalue'] = pervalue
        stat['process'] = slist
        statlist['status'] = stat
    except ValueError:
        statlist['status'] = 1
    return statlist


# 鏈接跟蹤
def check_ipconntrack():
    statlist = {}
    stat = {}
    try:
        procfile = ""
        version = commands.getoutput(
            "cat /etc/redhat-release | awk -F 'release' '{print $NF}' | awk -F '.' '{print $1}'").strip()
        if int(version) == 6 or int(version) == 7:
            procfile = "/proc/sys/net/netfilter/nf_conntrack_max"
        elif int(version) == 5:
            procfile = "/proc/sys/net/ipv4/ip_conntrack_max"
        line = commands.getoutput("grep nf_conntrack /proc/slabinfo|grep -v 'nf_conntrack_expect'")
        ip_conntrack = int(line.split()[1])
        ip_conmax = linecache.getline(procfile, 1)
        per_ipconn = round(Decimal(ip_conntrack) / Decimal(ip_conmax), 2)
        stat['ipconn'] = int(ip_conntrack)
        stat['max_ipconn'] = int(ip_conmax)
        stat['per_ipconn'] = per_ipconn
        statlist['status'] = stat
        linecache.clearcache()
    except:
        statlist['status'] = {}
    return statlist


##網絡監控##
# 網絡丟包,網絡丟包,路由跳數#
def check_net():
    statlist = {}
    stat = {}
    stat_t = {}
    dip_l = {u'TW': '203.69.109.117'}
    # dip_l = {u'TW': '203.69.109.117', u'KR': '58.229.180.29', u'US': '50.18.119.120',u'SG': '175.41.130.249', u'JP': '54.238.241.18', u'DE': '54.93.169.149'}
    if not os.path.exists("/bin/traceroute"):
        os.system("yum -y install traceroute >> /dev/null")
    try:
        for key in dip_l.keys():
            result = commands.getoutput("/bin/ping -c20 %s" % dip_l[key]).split('\n')
            stat['net_loss'] = result[-2].split(',')[2].split()[0]
            stat['net_delay'] = result[-1].split('=')[1].strip().split('/')[:-1]
            stat['net_delay'].append(result[-5].split('=')[-1].split()[0])
            trace = commands.getoutput("sudo /bin/traceroute -I %s" % dip_l[key]).split('\n')
            if trace[-1].split()[1] != "*" and trace[-1].split('(')[1].split(')')[0] == str(dip_l[key]):
                stat['strace'] = trace[-1].split()[0]
            elif trace[-1].split()[1] == "*":
                stat['trace'] = 30
            stat_t[key] = stat
        statlist['status'] = stat_t
    except ValueError:
        statlist['status'] = 1
    return statlist
check_net()

# tcp連接狀態#
def check_tcp():
    statlist = {}
    stat_dic = {}
    try:
        statl = ["ESTABLISHED", "LISTEN", "SYN_RECV", "SYN_SENT", "CLOSING", "CLOSED", "FIN_WAIT1", "FIN_WAIT2",
                 "TIME_WAIT", "LAST_ACK", "ITIME_WAIT", "CLOSE_WAIT"]
        for stat in statl:
            stat_wc = commands.getstatusoutput('netstat -tan | grep %s | wc -l' % stat)
            stat_dic[stat] = stat_wc[1]
        statlist['status'] = stat_dic
    except ValueError:
        statlist['status'] = {}
    return statlist

# 網卡流量，網卡IO，計費頻寬#
def get_nic():
    line = commands.getoutput("/sbin/ifconfig | /bin/grep 'Link encap:Ethernet'").split('\n')
    nic_info = [l.split()[0] for l in line]
    return nic_info

def check_net_flow():
    stat = {}
    statlist = {}
    nic_info = get_nic()
    nic_file = open('/proc/net/dev', 'r')
    try:
        linelist = [line for line in nic_file.readlines()]
        for nic in nic_info:
            for line in linelist:
                if line.find(nic) > 0:
                    stat[nic] = {}
                    stat[nic]['RX_Bytes'] = line.split()[1]
                    stat[nic]['RX_Packets'] = line.split()[2]
                    stat[nic]['RX_Errs'] = line.split()[3]
                    stat[nic]['RX_Drop'] = line.split()[4]
                    stat[nic]['TX_Bytes'] = line.split()[9]
                    stat[nic]['TX_Packets'] = line.split()[10]
                    stat[nic]['TX_Errs'] = line.split()[11]
                    stat[nic]['TX_Drop'] = line.split()[12]
        statlist['status'] = stat
    except ValueError:
        statlist['status'] = 1
    nic_file.close()
    return statlist

def make_json(func):
    func_status = func['status']
    if len(sys.argv) > 3:
        return func_status[sys.argv[2]][sys.argv[3]]
    elif len(sys.argv) > 2:
        return func_status[sys.argv[2]]
    else:
        dev = []
        for i in func_status.keys():
            dev += [{'{#NAME}': i}]
        return json.dumps({'data': dev}, sort_keys=True, indent=7, ensure_ascii=False, separators=(',', ':'))

#
# def main():
#     if sys.argv[1] == 'snmp_net':
#         func = check_snmp_net()
#     elif sys.argv[1] == 'load':
#         func = check_load()
#     elif sys.argv[1] == 'cpu':
#         func = check_cpu()
#     elif sys.argv[1] == 'mem':
#         func = check_mem()
#     elif sys.argv[1] == 'storage':
#         func = check_storage()
#     elif sys.argv[1] == 'io':
#         func = check_io()
#     elif sys.argv[1] == 'sys_process':
#         func = check_sys_process()
#     elif sys.argv[1] == 'login_user':
#         func = check_login_user()
#     elif sys.argv[1] == 'uptime':
#         func = check_uptime()
#     elif sys.argv[1] == 'ulimit':
#         func = check_ulimit()
#     elif sys.argv[1] == 'ipconntrack':
#         func = check_ipconntrack()
#     elif sys.argv[1] == 'net':
#         func = check_net()
#     elif sys.argv[1] == 'tcp':
#         func = check_tcp()
#     elif sys.argv[1] == 'net_flow':
#         func = check_net_flow()
#     else:
#         func = check_net_flow()
#     return make_json(func)
#
# # if __name__ == '__main__':
# #     print main()
