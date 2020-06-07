#!/usr/bin/env python2.7
# encoding:utf8

from __future__ import division
import os, json, commands, linecache, time, re, sys, subprocess
from decimal import Decimal
from collections import Counter
from Publiclass import get_cmd_path, config

reload(sys)
sys.setdefaultencoding('utf8')


class Check_SYS:
    # 主機負載
    def check_load(self):
        '''
        :return: {'status': {'load_15': '0.05', 'load_5': '0.03', 'load_1': '0.05'}}
        '''
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

    # CPU使用率
    def check_cpu(self):
        '''
        :return: {'status': {'cpu_si': 0.0, 'cpu_st': 0.0, 'cpu_idle': 80.0, 'cpu_count': 2, 'cpu_ni': 0.0, 'cpu_wa': 0.0, 'cpu_sys': 20.0, 'cpu_hi': 0.0, 'cpu_us': 0.0}}
        '''
        statlist = {}
        stat = {}
        try:
            result = commands.getoutput('grep -c "model name" /proc/cpuinfo')
            stat['cpu_count'] = int(result)
            alldata = commands.getoutput('top -bi -n 2 -d 0.02').split('\n')
            c = [i for i in alldata if 'Cpu(s):' in i]
            cpuinfo = c[1].replace('Cpu(s):', '').replace('%', ' ')
            line_l = [round(Decimal(i.strip().split(' ')[0]), 2) for i in cpuinfo.split(',')]
            stat['cpu_us'] = line_l[0]
            stat['cpu_sys'] = line_l[1]
            stat['cpu_ni'] = line_l[2]
            stat['cpu_idle'] = line_l[3]
            stat['cpu_wa'] = line_l[4]
            stat['cpu_hi'] = line_l[5]  # 硬中断（Hardware IRQ）占用CPU的百分比
            stat['cpu_si'] = line_l[6]  # 软中断（Software Interrupts）占用CPU的百分比
            stat['cpu_st'] = line_l[7]  # 虚拟机占用百分比
        except:
            stat = {}
        statlist['status'] = stat
        return statlist

    # 主機內存
    def check_mem(self):
        '''
        :return: {'status': {'virtual_percent': '0.00', 'physical_percent': 55.5}}
        '''
        statlist = {}
        stat = {}
        try:
            data = commands.getoutput('cat /proc/meminfo').split('\n')
            dev = {}
            for i in data:
                dev[i.split(':')[0]] = int(i.split()[1])
            physical_percent = round(
                Decimal(dev['MemTotal'] - dev['MemFree'] - dev['Buffers'] - dev['Cached']) / Decimal(
                    dev['MemTotal']) * 100,
                2)
            stat['physical_percent'] = physical_percent
            if dev['SwapTotal'] > 0:
                virtual_percent = round(Decimal(dev['SwapTotal'] - dev['SwapFree']) / Decimal(dev['SwapTotal']) * 100,
                                        2)
                stat['virtual_percent'] = virtual_percent
            else:
                stat['virtual_percent'] = '0.00'
            statlist['status'] = stat
        except ValueError:
            statlist['status'] = 1
        return statlist

    # 磁盤容量
    def check_storage(self):
        '''
        :return: {'status': {'tmpfs': {'inode': '1', 'size': '0'}, 'devtmpfs': {'inode': '1', 'size': '0'}, '/dev/vda1': {'inode': '7', 'size': '27'}}}
        '''
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
                stat[disk.split()[0]] = {'size': disk.split()[-2].replace('%', '')}
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
                stat[i.split()[0]].update({'inode': i.split()[-2].replace('%', '')})
            statlist['status'] = stat
        except ValueError:
            statlist['status'] = 1
        return statlist

    # 磁盤io
    def check_io(self):
        '''
        :return: {'status': {'vda': {'w_count': '22.08', 'r_count': '3.18', 'w_rate': '286.70', 'r_rate': '109.29', 'util': '1.40'}}}
        '''
        statlist = {}
        stat = {}
        iostat_bin = get_cmd_path('iostat')
        try:
            line = commands.getoutput('sudo /sbin/fdisk -l | /bin/grep "Disk" | grep -v "identifier"').split('\n')
            disklist = [i for i in line]
            disk_t = [i.split()[1].split(':')[0].split('/')[-1] for i in disklist]
            io_info = {}
            for disk in disk_t:
                stat_t = commands.getoutput('%s -x -k -d %s' % (iostat_bin, disk)).split('\n')[-2].split()
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

    # 系統進程
    def check_sys_process(self):
        '''
        :return: {'status': {'run': 1, 'unsleep': 0, 'zombie': 1, 'sleep': 179, 'stopped': 0, 'total': 181}}
        '''
        statlist = {}
        stat = {}
        try:
            sys_process = commands.getoutput("/bin/ps -el|grep -v grep |sed -n '2,$p'|awk '{print $2}'").split('\n')
            result = Counter(sys_process)
            stat['total'] = len(sys_process)
            stat['run'] = result['R']  # 运行
            stat['unsleep'] = result['D']  # 不可中断  uninterruptible sleep
            stat['sleep'] = result['S']  # 中断 sleeping
            stat['zombie'] = result['Z']  # 僵尸
            stat['stopped'] = result['T']  # 停止 traced or stopped
            statlist['status'] = stat
        except ValueError:
            statlist['status'] = 1
        return statlist

    # 登錄用戶数
    def check_login_user(self):
        '''
        :return: {'status': {'login_user': '1'}}
        '''
        statlist = {}
        stat = {}
        try:
            login_user = commands.getoutput("/usr/bin/who | /usr/bin/wc -l").split('\n')
            stat['login_user'] = int(login_user[0])
            statlist['status'] = stat
        except ValueError:
            statlist['status'] = 1
        return statlist

    # 运行时间 （以秒为单位）
    def check_uptime(self):
        '''
        :return: {'status': {'uptime': '1215990.41'}}
        '''
        statlist = {}
        stat = {}
        try:
            uptime = linecache.getline('/proc/uptime', 1).split()[0]
            stat['uptime'] = int(uptime.split('.')[0])
            statlist['status'] = stat
        except ValueError:
            statlist['status'] = 1
        return statlist

    def max_process(self):
        tmp = {}
        valuetmp = {}
        slist = ''
        lsof_bin = get_cmd_path('lsof')
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

    def check_ulimit(self):
        '''
        :return: {'status': {'process': '/usr/local/mysql/bin/mysqld:6432', 'pervalue': 0.0002, 'all_handle': '30488', 'max_handle': '1000000'}}
        '''
        statlist = {}
        stat = {}
        try:
            slist = self.max_process()
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
    def check_ipconntrack(self):
        '''
        :return: {'status': {'max_ipconn': 6553500, 'per_ipconn': 0.0, 'ipconn': 276}}
        '''
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
            line = commands.getoutput(
                "/usr/bin/grep nf_conntrack /proc/slabinfo|/usr/bin/grep -v 'nf_conntrack_expect'")
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

    ## 网络监控
    # 网络丟包,网络丟包,路由跳数#
    def check_net(self):
        '''
        :return:{'status': {'net_delay_max': '0.370', 'trace': '2', 'net_delay_avg': '0.323', 'net_delay_min': '0.286', 'net_loss': '0', 'net_delay_last': '0.370'}}
        '''
        statlist = {}
        stat = {}
        zabbix_agent_conf = config('net', 'zabbix_agent_conf')
        proxy_ip = commands.getoutput("/usr/bin/cat %s|grep 'ServerActive'|grep -v '^#'" % zabbix_agent_conf).split('=')[1].strip()
        traceroute_bin = get_cmd_path('traceroute')
        try:
            result = commands.getoutput("/bin/ping -c20 %s" % proxy_ip).split('\n')
            stat['net_loss'] = result[-2].split(',')[2].split()[0].split('%')[0]
            net_delay = result[-1].split('=')[1].strip().split('/')
            stat['net_delay_min'] = net_delay[0]
            stat['net_delay_avg'] = net_delay[1]
            stat['net_delay_max'] = net_delay[2]
            stat['net_delay_last'] = result[-5].split('=')[-1].split()[0]
            trace = commands.getoutput("sudo %s -I %s" % (traceroute_bin, proxy_ip)).split('\n')
            if trace[-1].split()[1] != "*" and trace[-1].split('(')[1].split(')')[0] == proxy_ip:
                stat['trace'] = trace[-1].split()[0]
            elif trace[-1].split()[1] == "*":
                stat['trace'] = 30
            statlist['status'] = stat
        except ValueError:
            statlist['status'] = 1
        return statlist

    # tcp連接狀態
    def check_tcp(self):
        '''
        :return: {'status': {'FIN_WAIT2': '0', 'ESTABLISHED': '3', 'FIN_WAIT1': '0', 'LAST_ACK': '0', 'ITIME_WAIT': '0', 'SYN_RECV': '0', 'TIME_WAIT': '0', 'CLOSED': '0', 'CLOSING': '0', 'SYN_SENT': '0', 'CLOSE_WAIT': '0', 'LISTEN': '15'}}
        '''
        statlist = {}
        stat_dic = {}
        try:
            statl = ["ESTABLISHED", "LISTEN", "SYN_RECV", "SYN_SENT", "CLOSING", "CLOSED", "FIN_WAIT1", "FIN_WAIT2",
                     "TIME_WAIT", "LAST_ACK", "ITIME_WAIT", "CLOSE_WAIT"]
            for stat in statl:
                stat_wc = commands.getstatusoutput('netstat -tan | grep %s | wc -l' % stat)
                stat_dic[stat] = int(stat_wc[1])
            statlist['status'] = stat_dic
        except ValueError:
            statlist['status'] = {}
        return statlist

    # 網卡流量，網卡IO，計費頻寬
    def get_nic(self):
        line = commands.getoutput("/sbin/ifconfig | /bin/grep -E 'Link encap|flags'|grep -v 'lo'").split('\n')
        nic_info = [l.split()[0].strip(':') for l in line]
        return nic_info

    def check_net_flow(self):
        '''
        :return: {'status': {'eth0': {'RX_Packets': '19896213', 'RX_Bytes': '1772717752', 'RX_Errs': '0', 'TX_Errs': '0', 'TX_Drop': '0', 'TX_Bytes': '2175796819', 'TX_Packets': '21454618', 'RX_Drop': '0'}}}
        '''
        stat = {}
        statlist = {}
        nic_info = self.get_nic()
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


def main():
    info = Check_SYS()
    func = getattr(info, 'check_' + sys.argv[1])()
    func_status = func['status']
    if len(sys.argv) > 3:
        return func_status[sys.argv[2]][sys.argv[3]]
    elif len(sys.argv) > 2:
        return func_status[sys.argv[2]]
    else:
        dev = []
        if sys.argv[1] == 'storage' or sys.argv[1] == 'io':
            for i in func['status'].keys():
                dev += [{'{#FSNAME}': i}]
        elif sys.argv[1] == 'net_flow':
            for i in func['status'].keys():
                dev += [{'{#IFNAME}': i}]
        else:
            keyinfo = {}
            for i in func_status.keys():
                keyinfo['{#%s}' % i.upper()] = i
            dev = [keyinfo]
        return json.dumps({'data': dev}, sort_keys=True, indent=7, ensure_ascii=False, separators=(',', ':'))


if __name__ == '__main__':
    print main()
