#!/usr/bin/python2.7
# encoding:utf8

import os, sys, re, commands, datetime, telnetlib, urllib, traceback, string, pymysql
from decimal import Decimal
from Publiclass import *
from json import loads


def get_cmd_path(cmd):
    cmd_path = commands.getoutput('/usr/bin/which %s' % cmd).split('\n')[0]
    return cmd_path


# java應用狀態
def get_jvm_info():
    jps_cmd = get_cmd_path('jps')
    jvm_list = commands.getoutput('%s -m' % jps_cmd).split('\n')
    if 'command not found' in jvm_list or 'No such file or directory' in jvm_list:
        return 1
    else:
        jvm_info = {}
        for res in jvm_list:
            if res.split()[1] == 'WatchdogManager' or res.split()[1] == 'Jps':
                pass
            else:
                jvm_info[res.split()[-2]] = res.split()[0]
        return jvm_info


def get_jvm_value(pid):
    jvm_value = {}
    try:
        #	堆內存使用
        jmap_cmd = get_cmd_path('jmap')
        result = commands.getoutput('%s -histo:live %s' % (jmap_cmd,pid)).split('\n')
        result = result[3:]
        if int(result[0].split()[0].split(':')[0].strip()) == 1:
            jvm_value['mem_max'] = result[0].split()[2]
        if result[-1].split()[0] == 'Total':
            jvm_value['mem_total'] = result[-1].split()[-1]
        #	類加載信息
        jstat_cmd = get_cmd_path('jstat')
        result_1 = commands.getoutput('%s -class %s' % (jstat_cmd,pid)).split('\n')
        jvm_value['load_class'] = result_1[1].split()[0].strip()
        jvm_value['unload_class'] = result_1[1].split()[2]
        jvm_value['load_time'] = result_1[1].split()[-1]
        #	三代內存使用
        result_2 = commands.getoutput('%s -gcutil %s' % (jstat_cmd,pid)).split('\n')
        if len(result_2) == 2:
            keys = result_2[0].split()
            values = result_2[1].split()
            data = dict(zip(keys, values))
            jvm_value['S0_men'] = data['S0']
            jvm_value['S1_men'] = data['S1']
            jvm_value['E_men'] = data['E']
            jvm_value['O_men'] = data['O']
            if 'P' in data.keys(): jvm_value['P_men'] = data['P']
            if 'M' in data.keys(): jvm_value['M_men'] = data['M']
            if 'CCS' in data.keys(): jvm_value['CCS_men'] = data['CCS']
            if 'GCT' in data.keys(): jvm_value['GCT_men'] = data['GCT']
            #	垃圾回收信息
            jvm_value['YGC'] = round(Decimal(60) / Decimal(int(data['YGC'])), 3)
            jvm_value['YGCT'] = round(Decimal(data['YGCT']) / Decimal(int(data['YGC'])), 3)
            jvm_value['FGC'] = round(Decimal(60) / Decimal(int(data['FGC'])), 3)
            jvm_value['FGCT'] = round(Decimal(data['FGCT']) / Decimal(int(data['FGC'])), 3)
        else:
            print "三代內存查詢有問題"
    except:
        jvm_value = {}
    return jvm_value


def check_jvm(itemname):
    '''
    :param itemname: 进程名， 格式 --> /usr/local/jdk/bin/jps -m 查出的进程名
    :return:
    '''
    statlist, stat = {}, {}
    jvm_info = get_jvm_info()
    # print jvm_info
    try:
        statlist[itemname] = get_jvm_value(jvm_info[itemname])
        stat['status'] = statlist
    except:
        stat['status'] = {}
    return stat

# print check_jvm('Elasticsearch')
# {'status': {'Elasticsearch': {'YGC': 4.286, 'YGCT': 0.034, 'unload_class': '39', 'load_class': '13726', 'FGCT': 0.123, 'S1_men': '0.00', 'GCT_men': '4.170', 'CCS_men': '83.82', 'mem_max': '18395352', 'mem_total': '54683096', 'O_men': '6.15', 'load_time': '5.22', 'S0_men': '0.00', 'FGC': 2.0, 'E_men': '0.50', 'M_men': '92.28'}}}

def rsync_get_last_n_lines(logfile):
    vtime = ((datetime.datetime.now() - datetime.timedelta(hours=8) - datetime.timedelta(minutes=1)).strftime(
        "%Y/%m/%d %H:%M"))
    time1 = vtime.split()[0]
    time2 = vtime.split()[1]
    blk_size_max = 163840
    n_lines = []
    if os.path.exists(logfile):
        fp = open(logfile, 'rU')
        fp.seek(0, 2)
        cur_pos = fp.tell()
        num = 0
        while cur_pos > 0 and num != 2:
            blk_size = min(blk_size_max, cur_pos)
            fp.seek(cur_pos - blk_size, 0)
            blk_data = fp.read(blk_size)
            assert len(blk_data) == blk_size
            lines = blk_data.split('\n')
            for line in reversed(lines):
                if re.match(u'\d{4}\/\d{2}\/\d{2}\s+\d{2}:\d{2}.*sent [0-9].*bytes+\s+received', line):
                    if line.split()[0] == time1 and line.split()[1][:5] == time2:
                        n_lines.append(line)
                    elif int(time.mktime(time.strptime(' '.join(line.split()[:2]), '%Y/%m/%d %H:%M:%S'))) > int(
                            time.mktime(time.strptime((datetime.datetime.now() - datetime.timedelta(
                                hours=8) - datetime.timedelta(minutes=1)).strftime("%a %b %d %H:%M %Y"),
                                                      '%a %b %d %H:%M %Y'))):
                        num = 1
                    else:
                        num = 2
            if len(lines) > 1 and len(lines[0]) > 0:
                cur_pos -= (blk_size - len(lines[0]))
            else:
                cur_pos -= blk_size
            fp.seek(cur_pos, 0)
        if len(n_lines) > 0 and len(n_lines[-1]) == 0:
            del n_lines[-1]
        fp.close()
    else:
        return 1
    return n_lines


# rsync應用狀態
def check_rsync(logfile):
    stat, statlist = {}, {}
    # logfile = '/var/log/rsyncd.log'
    sent, received = [], []
    n_lines = rsync_get_last_n_lines(logfile)
    if type(n_lines) == list:
        for line in rsync_get_last_n_lines(logfile):
            sent.append(int(line.split()[4]))
            received.append(int(line.split()[7]))
        if len(sent) == 0:
            sentv = 0
        else:
            sentv = int(sum(sent) / 1000)
        if len(received) == 0:
            receivedv = 0
        else:
            receivedv = int(sum(received) / 1000)
        line = commands.getoutput("/bin/ps -ef | /bin/grep -v grep | /bin/grep rsync | /usr/bin/wc -l").split('\n')[0]
        statlist['process'] = line
        statlist['sentv'] = sentv
        statlist['receivedv'] = receivedv
        stat['status'] = statlist
    else:
        stat['status'] = {}
    return stat


# dns應用狀態
def getip():
    html = urllib.urlopen("http://ifconfig.io/")
    for line in html.read().split('\n'):
        if 'IP Address' in line:
            ip = line.split('>')[3].split('<')[0]
    return ip


def check_bind():
    ip = getip()
    res = commands.getoutput('dig +short www.gamedreamer.com.tw @%s | wc -l' % ip).split('\n')
    if int(res[0]) >= 1:
        return res[0]
    else:
        return 0


def check_dns():
    stat = {}
    statlist = {}
    try:
        res = commands.getoutput('/sbin/pidof named | grep -v ^$ | wc -l').split('\n')
        res_ser = int(res[0])
        statlist['res_ser'] = res_ser
        statlist['res_bind'] = check_bind()
    except:
        statlist = {}
    stat['status'] = statlist
    return stat


# vsftp應用狀態
def vsftp_get_last_n_lines(logfile):
    now_time = int(time.time() - 60)
    blk_size_max = 163840
    n_lines = []
    if os.path.exists(logfile):
        fp = open(logfile, 'rU')
        fp.seek(0, 2)
        cur_pos = fp.tell()
        num = 0
        while cur_pos > 0 and num != 2:
            blk_size = min(blk_size_max, cur_pos)
            fp.seek(cur_pos - blk_size, 0)
            blk_data = fp.read(blk_size)
            assert len(blk_data) == blk_size
            lines = blk_data.split('\n')
            for line in reversed(lines):
                if 'pid' in line:
                    mtime = line.split('[')[0].strip()
                    if int(time.mktime(time.strptime(mtime, "%a %b %d %H:%M:%S %Y"))) > now_time:
                        n_lines.append(line)
                        num = 1
                    else:
                        num = 2
            # adjust cur_pos
            if len(lines) > 1 and len(lines[0]) > 0:
                cur_pos -= (blk_size - len(lines[0]))
            else:
                cur_pos -= blk_size
            fp.seek(cur_pos, 0)
        if len(n_lines) > 0 and len(n_lines[-1]) == 0:
            del n_lines[-1]
        fp.close()
    else:
        return 1
    return n_lines


def check_vsftpd(logfile):
    stattlist = {}
    # logfile = '/var/log/vsftpd.log'
    n_lines = vsftp_get_last_n_lines(logfile)
    if type(n_lines) == list:
        statlist = ['LOGIN', 'FAIL', 'UPLOAD', 'DOWNLOAD', 'DELETE', 'RENAME', 'UP_SIZE', 'DO_SIZE', 'AVG_UP', 'AVG_DO']
        status = {'LOGIN': 0, 'FAIL': 0, 'UPLOAD': 0, 'DOWNLOAD': 0, 'DELETE': 0, 'RENAME': 0, 'UP_SIZE': 0,
                  'DO_SIZE': 0, 'AVG_UP': 0, 'AVG_DO': 0}
        avgup, avgdo, unum, dnum, ok_stat = 0, 0, 0, 0, 0
        for line in vsftp_get_last_n_lines(logfile):
            for stat in statlist[:6]:
                if stat in line:
                    status[stat] = status[stat] + 1
            if re.match(u'.*] OK ', line):
                ok_stat = ok_stat + 1
            if re.match(u'.*[0-9] bytes,', line) and len(line.split(',')) >= 4:
                if 'UPLOAD' in line:
                    status['UP_SIZE'] = status['UP_SIZE'] + int(line.split(',')[2].split()[0])
                elif 'DOWNLOAD' in line:
                    status['DO_SIZE'] = status['DO_SIZE'] + int(line.split(',')[2].split()[0])
            if re.match(u'.*[0-9]Kbyte/sec', line) and len(line.split(',')) >= 4:
                if 'UPLOAD' in line:
                    avgup = status['AVG_UP'] + string.atof(line.split(',')[3].replace('Kbyte/sec', '').replace(' ', ''))
                    unum = unum + 1
                elif 'DOWNLOAD' in line:
                    avgdo = status['DO_SIZE'] + string.atof(
                        line.split(',')[3].replace('Kbyte/sec', '').replace(' ', ''))
                    dnum = dnum + 1
        if unum != 0:
            status['AVG_UP'] = avgup / unum
        if dnum != 0:
            status['AVG_DO'] = avgdo / dnum
    else:
        status = {}
    stattlist['status'] = status
    return stattlist


# ssh應用狀態#
def ssh_get_last_n_lines():
    now_time = (datetime.datetime.now() - datetime.timedelta(minutes=1)).strftime("%b %d %H:%M:%S %Y").split()
    blk_size_max = 163840
    n_lines = []
    fp = open('/var/log/secure', 'rU')
    fp.seek(0, 2)
    cur_pos = fp.tell()
    num = 0
    while cur_pos > 0 and num != 2:
        blk_size = min(blk_size_max, cur_pos)
        fp.seek(cur_pos - blk_size, 0)
        blk_data = fp.read(blk_size)
        assert len(blk_data) == blk_size
        lines = blk_data.split('\n')
        for line in reversed(lines):
            #			if re.match(u'[A-Z]+[a-z]{2} \d{2} \d{2}:\d{2}:\d{2}.*sshd',line):
            if re.match(u'.*sshd.*', line):
                line_time = (' '.join(line.split()[:3]) + ' ' + now_time[3]).split()
                if line_time[0] == now_time[0] and str(line_time[1]).zfill(2) == now_time[1] and now_time[2].split(':')[
                                                                                                 :2] == line_time[
                                                                                                            2].split(
                    ':')[:2]:
                    n_lines.append(line)
                elif int(time.mktime(time.strptime(' '.join(line_time), '%b %d %H:%M:%S %Y'))) > int(time.mktime(
                        time.strptime(
                            (datetime.datetime.now() - datetime.timedelta(minutes=1)).strftime("%a %b %d %H:%M %Y"),
                            '%a %b %d %H:%M %Y'))):
                    num = 1
                else:
                    num = 2
        # adjust cur_pos
        if len(lines) > 1 and len(lines[0]) > 0:
            cur_pos -= (blk_size - len(lines[0]))
        else:
            cur_pos -= blk_size
        fp.seek(cur_pos, 0)
    if len(n_lines) > 0 and len(n_lines[-1]) == 0:
        del n_lines[-1]
    fp.close()
    return n_lines


'''
def ssh_get_last_n_lines():
    now_str = (datetime.datetime.now() - datetime.timedelta(minutes=1)).strftime("%b %d %H:%M")
    cmd = "cat /var/log/secure | grep sshd|grep '{0}'".format(now_str)
    ret = commands.getoutput(cmd)
    if ret:
        n_lines = ret.split("\n")
    else:
        n_lines = []
    return  n_lines
'''


def check_ssh():
    stat = {}
    try:
        statlist = {'Failed_password': 0, 'Accepted_password': 0, 'Root_opened': 0, 'Order_opened': 0, 'Root_closed': 0,
                    'Order_closed': 0}
        for line in ssh_get_last_n_lines():
            if re.match(u'.*Failed password ', line): statlist['Failed_password'] = statlist['Failed_password'] + 1
            if re.match(u'.*Accepted password ', line): statlist['Accepted_password'] = statlist[
                                                                                            'Accepted_password'] + 1
            if re.match(u'.*session opened for user root ', line): statlist['Root_opened'] = statlist['Root_opened'] + 1
            if re.match(u'.*session opened for user ', line): statlist['Order_opened'] = statlist['Order_opened'] + 1
            if re.match(u'.*session closed for user root ', line): statlist['Root_closed'] = statlist['Root_closed'] + 1
            if re.match(u'.*session closed for user ', line): statlist['Order_closed'] = statlist['Order_closed'] + 1
    except:
        statlist = {}
    stat['status'] = statlist
    return stat


# haproxy應用狀態,要注意socat命令是否存在
# 後端server隊列，狀態，會話，每秒流量，錯誤連接
def get_status(ser_name):
    timeint = 20
    statlist = {}
    #	vlist = ['session_total','byte_in','byte_out','deny_req'.'deny_resp','error_req','error_conn','']
    status, output = commands.getstatusoutput('echo "show stat" |  socat stdio unix-connect:/tmp/haproxy')
    for line in output.split('\n'):
        if ser_name in line and 'FRONTEND' not in line and 'BACKEND' not in line:
            Byte_IN = line.split(',')[8]
            Byte_out = line.split(',')[9]
            deny_resp = line.split(',')[11]
            err_conn = line.split(',')[13]
            err_resp = line.split(',')[14]
    time.sleep(timeint)
    status, output = commands.getstatusoutput('echo "show stat" |  socat stdio unix-connect:/tmp/haproxy')
    for line in output.split('\n'):
        if ser_name in line and 'FRONTEND' not in line and 'BACKEND' not in line:
            statlist['qcur'] = line.split(',')[2]
            statlist['qmax'] = line.split(',')[3]
            statlist['scur'] = line.split(',')[4]
            statlist['smax'] = line.split(',')[5]
            statlist['slim'] = line.split(',')[6]
            statlist['Byte_IN'] = abs(int(Byte_IN) - int(line.split(',')[8])) / timeint
            statlist['Byte_out'] = abs(int(Byte_out) - int(line.split(',')[9])) / timeint
            statlist['deny_resp'] = abs(int(deny_resp) - int(line.split(',')[11])) / timeint
            statlist['err_conn'] = abs(int(err_conn) - int(line.split(',')[13])) / timeint
            statlist['err_resp'] = abs(int(err_resp) - int(line.split(',')[14])) / timeint
            statlist['status'] = line.split(',')[17]
    return statlist


def check_haproxy():
    stat = {}
    statlist = {}
    sock_file = "/tmp/haproxy"
    if os.path.exists('/usr/bin/socat'):
        pass
    else:
        status, output = commands.getstatusoutput('yum list | grep socat >> /dev/null')
        if int(status) != 0:
            os.system(
                'wget –no-cache http://www.convirture.com/repos/definitions/rhel/6.x/convirt.repo -O /etc/yum.repos.d/convirt.repo')
        else:
            os.system('yum -y install socat')
    if os.path.exists(sock_file):
        out = open("/usr/local/haproxy/conf/haproxy.cfg", 'r').readlines()
        for line in out:
            #			if re.match(u'#',line) or line == '' or 'FRONTEND'  in line or 'BACKEND' in line:pass
            if re.match(u'#', line):
                pass
            #			elif 'server' in line and 'weight' in line :
            elif 'listen' in line and 'admin_stats' not in line:
                ser_name = line.split()[1]
                stat[ser_name] = get_status(ser_name)
    else:
        stat = {}
    statlist['status'] = stat
    return statlist


# keepalived應用狀態
def get_vip():
    result = commands.getoutput('/sbin/ip a')
    count = 0
    for line in result.split('\n'):
        if re.match(u".*inet \d{1,3}\.\d{1,3}\.\d{1,3}.\d{1,3}/+\d{1,2} scope global", line):
            count += 1
    return count


def check_keepalived():
    statlist = {}
    stat = {}
    try:
        statlist['vip_c'] = get_vip()
        res = commands.getoutput('pidof keepalived | grep -v ^$ | wc -l').split('\n')
        ser_status = int(res[0])
        if ser_status >= 1:
            statlist['ser_status'] = 1
    except:
        statlist = {}
    stat['status'] = statlist
    return stat


# lvs應用狀態#
def get_lvs_ip():
    ip_list = []
    result = commands.getoutput('/sbin/ip a | /bin/grep "scope global eth0"').split('\n')
    for row in result:
        if re.match(u'.*inet \d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/+\d{1,2} scope global eth0', row):
            ip_list.append(row.split()[1].split('/')[0])
    return ip_list


class Command(object):
    def vrrp_stats(self, timeout=None):
        def target():
            try:
                self.process = subprocess.Popen("/usr/sbin/tcpdump -t vrrp -n", stdout=subprocess.PIPE,
                                                stderr=subprocess.PIPE, shell=True)
                #				self.process = subprocess.Popen("top",stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)
                self.output, self.error = self.process.communicate()
                self.status = self.process.returncode
            except:
                self.error = traceback.format_exc()
                self.status = -1

        thread = threading.Thread(target=target)
        thread.start()
        thread.join(timeout)
        if thread.isAlive():
            os.system('/bin/kill %s' % self.process.pid)
            thread.join()
        return self.status, self.output, self.error


def check_lvs():
    statlist = {}
    stat = {}
    lvs_real = commands.getoutput(
        "/sbin/ipvsadm -ln | grep -E  '\->' | grep -v 'Port' | sed 's/\:/_/g' | awk '{print $2,$5,$6}'").split('\n')
    statlist['vip_list'] = get_lvs_ip()
    statlist['lvs_real'] = lvs_real
    command = Command()
    status, output, error = command.vrrp_stats(timeout=50)
    try:
        for row in error.split('\n'):
            if re.match(u'.*packets captured', row):
                statlist['packet'] = int(row.split()[0]) * 60 / 50
    #		for row in output.split('\n'):
    #			if len(row) >= 2 and re.match(u'\d{1,3}\.\d{1,3}\.\d{1,3}.\d{1,3}',row.split()[1]):
    #				if row.split()[1] in iptmp.keys():
    #					iptmp[row.split()[1]] += 1
    #				else:iptmp[row.split()[1]] = 1
    #		for row in iptmp.keys():
    #			vrr_status[row] = int(iptmp[row])*60/50
    except:
        statlist['packet'] = 0
    stat['status'] = statlist
    return stat


# redis應用狀態
def get_redis_pass():
    passwd = 1
    try:
        conf = "/etc/redis/redis.conf"
        if not os.path.exists(conf):
            conf = "/usr/local/redis/etc/redis.conf"
        cf = open(conf, 'r').readlines()
        for line in cf:
            if 'requirepass' in line:
                if not re.match(u'#', line):
                    passwd = line.split()[1]
        return passwd
    except:
        return 1

def check_redis(port=6379):
    stat_t = {}
    stat = {}
    try:
        result = commands.getoutput("/usr/bin/free |grep Mem|awk -F ' ' '{print $2}'")
        stat_t['maxmemory'] = int(result)
        binfile = get_cmd_path("redis-cli")
        info_value = {}
        passwd = get_redis_pass()
        if passwd == 1:
            result = commands.getoutput("%s -p %s -c info " % (binfile, port)).split('\n')
        else:
            result = commands.getoutput("%s -p %s -a %s -c info " % (binfile, port, passwd)).split('\n')
        for row in result:
            if not re.match(u'#', row) and len(row.replace('\r', '')) != 0:
                info_value[row.split(':')[0]] = row.replace('\r', '').split(':')[1]
        nlist = ['redis_version', 'uptime_in_seconds', 'rdb_last_save_time', 'rdb_changes_since_last_save',
                    'used_memory', 'used_memory_peak', 'expired_keys', 'evicted_keys', 'keyspace_hits',
                    'keyspace_misses', 'latest_fork_usec', 'blocked_clients', 'connected_slaves',
                    'connected_clients', 'total_connections_received', 'total_commands_processed']
        if info_value['role'] == 'master' and info_value['connected_slaves'] == '0':
            namelist = nlist
        else:
            namelist = nlist.append('master_link_status')
        for key in info_value.keys():
            if key in namelist:
                stat_t[key] = info_value[key]
        if int(stat_t['keyspace_misses']) + int(stat_t['keyspace_hits']) == 0:
            stat_t['keyspace_hits_rate'] = 0
        else:
            stat_t['keyspace_hits_rate'] = round(
                int(stat_t['keyspace_hits']) / (int(stat_t['keyspace_misses']) + int(stat_t['keyspace_hits'])), 4)
        stat_t['used_memory'] = int(int(stat_t['used_memory']))
        stat_t['used_memory_peak'] = int(int(stat_t['used_memory_peak']))
        stat['status'] = stat_t
    except:
        stat = {}
    return stat

# print check_redis('6379')

# jdbc應用狀態#

# mycat應用狀態
'''
	顯示後端連接信息：show @@backend
	顯示當前客戶端連接情況：show @@connection
	顯示當前線程池的執行情況：show @@threadpool (前者處理積壓，後者為待處理積壓)
	顯示後端心跳信息：show @@heartbeat (RS_CODE为1表示心跳正常)
	顯示數據節點訪問情況：show @@datanode (包括每个数据节点当前活动连接数(active),空闲连接数（idle）以及最大连接数(maxCon) size，EXECUTE参数表示从该节点获取连接的次数)
	顯示當前processor的處理情況： show @@processor (processor的IO吞吐量(NET_IN/NET_OUT)、IO队列的积压情况(R_QUEY/W_QUEUE)，Socket Buffer Pool的使用情况BU_PERCENT为已使用的百分比、BU_WARNS为Socket Buffer Pool不够时，临时创新的新的BUFFER的次数，若百分比经常超过90%并且BU_WARNS>0，则表明BUFFER不够，需要增大)
	顯示數據源的情況：show @@datasource (節點的讀寫性)
	顯示緩存的使用情況：show @@cache (CUR为当前已经在缓存中的数量，ACESS为缓存读次数，HIT为缓存命中次数，PUT 为写缓存次数，LAST_XX为最后操作时间戳,若CUR接近MAX，而PUT大于MAX很多，则表明MAX需要增大，HIT/ACCESS为缓存命中率，这个值越高越好)
'''


def Mysql(hostname, user, password, dport=3306, socket='/tmp/mysql.sock'):
    conn = pymysql.connect(host=hostname, user=user, passwd=password, port=dport, unix_socket=socket)
    cur = conn.cursor()
    return cur


def get_connection(hostname, user, password, dport=3306, socket='/tmp/mysql.sock'):
    # mycat連接數
    stat = {}
    cur = Mysql(hostname, user, password, dport, socket)
    sql = 'show @@connection;'
    cur.execute(sql)
    stat['mycat_conn'] = len(cur.fetchall())
    cur.close()
    return stat


def get_thread_value(hostname, user, password, dport=3306, socket='/tmp/mysql.sock'):
    # 調度積壓，線程積壓
    stat = {}
    cur = Mysql(hostname, user, password, dport, socket)
    sql = 'show @@threadpool'
    cur.execute(sql)
    for row in cur.fetchall():
        if 'Timer' in row:
            #			stat['timer'] = round(Decimal(int(row[3])) / Decimal(int(row[5])) * 100,2)
            time_TASK_QUEUE_SIZE = int(row[3])
            time_TOTAL_TASK = int(row[5])
        elif 'BusinessExecutor' in row:
            #			stat['thread_Executor'] = round(Decimal(int(row[3]))/Decimal(int(row[5])) * 100,2)
            Executor_TASK_QUEUE_SIZE = int(row[3])
            Executor_TOTAL_TASK = int(row[5])
    timeint = 10
    time.sleep(timeint)
    cur.execute(sql)
    for row in cur.fetchall():
        if 'Timer' in row:
            try:
                stat['time_queue'] = round(Decimal(int(row[3]) - time_TASK_QUEUE_SIZE) / Decimal(
                    int(row[5]) - time_TOTAL_TASK) / timeint * 100, 2)
            except:
                stat['time_queue'] = round(Decimal('0'), 2)
        elif 'BusinessExecutor' in row:
            try:
                stat['Executor_queue'] = round(Decimal(int(row[3]) - Executor_TASK_QUEUE_SIZE) / Decimal(
                    int(row[5]) - Executor_TOTAL_TASK) / timeint * 100, 2)
            except:
                stat['Executor_queue'] = round(Decimal('0'), 2)
    cur.close()
    return stat


def get_process(hostname, user, password, dport=3306, socket='/tmp/mysql.sock'):
    tmp = {}
    stat = {}
    statlist = {}
    cur = Mysql(hostname, user, password, dport, socket)
    sql = 'show @@processor'
    cur.execute(sql)
    for row in cur.fetchall():
        tmp[row[0]] = [row[1], row[2], row[4], row[5], row[9]]
    timeint = 10
    time.sleep(timeint)
    cur.execute(sql)
    for row in cur.fetchall():
        stat[row[0]] = {}
        stat[row[0]]['NET_IN'] = round((Decimal(int(row[1])) - Decimal(int(tmp[row[0]][0]))) / timeint, 2)
        stat[row[0]]['NET_OUT'] = round((Decimal(int(row[2])) - Decimal(int(tmp[row[0]][1]))) / timeint, 2)
        stat[row[0]]['R_QUEUE'] = round((Decimal(int(row[4])) - Decimal(int(tmp[row[0]][2]))) / timeint, 2)
        stat[row[0]]['W_QUEUE'] = round((Decimal(int(row[5])) - Decimal(int(tmp[row[0]][3]))) / timeint, 2)
        stat[row[0]]['BU_PERCENT'] = round(Decimal(int(row[8])), 2)
        stat[row[0]]['BU_WARNS'] = round((Decimal(int(row[9])) - Decimal(int(tmp[row[0]][4]))) / timeint, 2)
    cur.close()
    statlist['process'] = stat
    return statlist


# 後端節點
def get_reinfo(hostname, user, password, dport=3306, socket='/tmp/mysql.sock'):
    stat = {}
    cur = Mysql(hostname, user, password, dport, socket)
    sql = 'show @@heartbeat'
    cur.execute(sql)
    for row in cur.fetchall():
        stat[str(row[1])] = {}
        stat[str(row[1])]['heart'] = int(row[4])
    return stat


# 數據節點
def get_dninfo(hostname, user, password, dport=3306, socket='/tmp/mysql.sock'):
    stat = {}
    statlist = {}
    tmp = {}
    cur = Mysql(hostname, user, password, dport, socket)
    sql = "show @@datanode"
    cur.execute(sql)
    for row in cur.fetchall():
        tmp[str(row[0])] = []
        tmp[str(row[0])] = [int(row[7])]
    timeint = 10
    time.sleep(timeint)
    cur.execute(sql)
    for row in cur.fetchall():
        stat[row[0]] = {}
        stat[row[0]]['execut_s'] = round((Decimal(int(row[7]) - tmp[row[0]][0])) / timeint, 2)
        stat[row[0]]['max_conn_limit'] = int(row[6])
        stat[row[0]]['max_sql'] = int(row[-2])
    cur.close()
    statlist['datanode'] = stat
    return statlist


# 緩存情況

def get_cache(hostname, user, password, dport=3306, socket='/tmp/mysql.sock'):
    stat = {}
    cur = Mysql(hostname, user, password, dport, socket)
    sql = "show @@cache"
    cur.execute(sql)
    for row in cur.fetchall():
        if 'SQLRouteCache' in row:
            #			stat['hit'] = round(Decimal(int(row[4]))/Decimal(int(row[3])) * 100,2)
            #			stat['cur'] = round(Decimal(int(row[2]))/Decimal(int(row[1])) * 100,2)
            stat['MAX'] = int(row[1])
            stat['CUR'] = int(row[2])
            stat['HIT'] = int(row[4])
    cur.close()
    return stat


def check_mycat(hostname, user, password, dport=3306, socket='/tmp/mysql.sock'):
    statlist = {}
    try:
        stat = dict(get_connection(hostname, user, password, dport, socket).items() +
                    get_thread_value(hostname, user, password, dport, socket).items() +
                    get_process(hostname, user, password, dport, socket).items() +
                    get_dninfo(hostname, user, password, dport, socket).items() +
                    get_cache(hostname, user, password, dport, socket).items())
    except:
        stat = {}
    statlist['status'] = stat
    return statlist


# print check_mycat('localhost', 'root', 'qwe123', 3306, '/var/run/mysqld/mysqld.sock')


###nginx應用狀態
def check_nginx(url):
    # url:http://tsnginx.efun.com/nginx_status
    timeint = 60
    stat = {}
    statlist = {}
    c, html = mypycurl(url)
    try:
        c.perform()
        listvalue = html.getvalue().split(' ')
        serveraccpts = int(listvalue[7])
        handled = int(listvalue[8])
        requests = int(listvalue[9])
    except:
        return 0
    time.sleep(timeint)
    c, html = mypycurl(url)
    try:
        c.perform()
        listvalue = html.getvalue().split(' ')
        stat['activeConn'] = listvalue[2]
        stat['serveraccepts'] = abs(int(listvalue[7]) - serveraccpts) / timeint
        stat['handled'] = abs(int(listvalue[8]) - handled) / timeint
        stat['requests'] = abs(int(listvalue[9]) - requests) / timeint
        stat['reading'] = listvalue[11]
        stat['writing'] = listvalue[13]
        stat['waiting'] = listvalue[15]
        stat['http_code'] = c.getinfo(pycurl.HTTP_CODE)
        stat['http_total_time'] = c.getinfo(pycurl.TOTAL_TIME)
    except:
        stat = {}
    c.close()
    statlist['status'] = stat
    return statlist


# print check_nginx('http://tsnginx.efun.com/nginx_status')


##php應用狀態

def check_php(url):
    timeint = 60
    stat = {}
    statlist = {}
    t = Test()
    c, html = mypycurl(url)
    try:
        c.perform()
        alldata = loads(html.getvalue())
        accept_conn = alldata['accepted conn']
    except:
        return 0
    time.sleep(timeint)
    t = Test()
    c, html = mypycurl(url)
    try:
        c.perform()
        alldata = loads(html.getvalue())
        process_manager = alldata['process manager']
        uptime = alldata['start since']
        if 'accept_conn' in dir():
            accept_conn = round(abs(int(alldata['accepted conn']) - int(accept_conn) / timeint), 2)
        else:
            accept_conn = alldata['accepted conn']
        stat['accept_conn'] = accept_conn
        stat['listen_queue'] = alldata['listen queue']
        stat['max_listen_queue'] = alldata['max listen queue']
        stat['active_processes'] = alldata['active processes']
        stat['total_processes'] = alldata['total processes']
        stat['max_active_processes'] = alldata['max active processes']
        stat['max_children_reached'] = alldata['max children reached']
        stat['http_code'] = c.getinfo(pycurl.HTTP_CODE)
        stat['http_total_time'] = c.getinfo(pycurl.TOTAL_TIME)
    except:
        stat = {}
    c.close()
    statlist['status'] = stat
    return statlist


# print check_php('http://tsnginx.efun.com/nginx_status')

# monogo應用狀態

def check_mongo(url):
    timeint = 6
    #	url = 'http://localhost:28017/_status'
    datav = {}
    statlist = {}
    try:
        c, html = mypycurl(url)
        c.perform()
        print html.getvalue()
        alldata = loads(html.getvalue())
        http_code = c.getinfo(pycurl.HTTP_CODE)
        http_total_time = c.getinfo(pycurl.TOTAL_TIME)
        backgroundFlushing_flushes = alldata['serverStatus']['backgroundFlushing']['flushes']
        network_bytesIn = alldata['serverStatus']['network']['bytesIn']
        network_bytesOut = alldata['serverStatus']['network']['bytesOut']
        opcounters_command = alldata['serverStatus']['opcounters']['command']
        opcounters_delete = alldata['serverStatus']['opcounters']['delete']
        opcounters_getmore = alldata['serverStatus']['opcounters']['getmore']
        opcounters_insert = alldata['serverStatus']['opcounters']['insert']
        opcounters_query = alldata['serverStatus']['opcounters']['query']
        opcounters_update = alldata['serverStatus']['opcounters']['update']
        c.close()
    except:
        datav = {}
    time.sleep(timeint)
    try:
        c, html = mypycurl(url)
        c.perform()
        alldata = loads(html.getvalue())
        datav['mversion'] = alldata['serverStatus']['version']
        datav['uptime'] = alldata['serverStatus']['uptime']
        datav['backgroundFlushing_average_ms'] = round(alldata['serverStatus']['backgroundFlushing']['average_ms'], 2)
        datav['backgroundFlushing_flushes'] = (alldata['serverStatus']['backgroundFlushing'][
                                                   'flushes'] - backgroundFlushing_flushes) / timeint
        datav['backgroundFlushing_last_ms'] = alldata['serverStatus']['backgroundFlushing']['last_ms']
        datav['connections_current'] = alldata['serverStatus']['connections']['current']
        datav['indexCounters_missRatio'] = (1 - round(alldata['serverStatus']['indexCounters']['missRatio'], 2)) * 100
        datav['indexCounters_resets'] = alldata['serverStatus']['indexCounters']['resets']
        datav['mem_mapped'] = alldata['serverStatus']['mem']['mapped']
        datav['mem_resident'] = alldata['serverStatus']['mem']['resident']
        datav['mem_virtual'] = alldata['serverStatus']['mem']['virtual']
        datav['network_bytesIn'] = (alldata['serverStatus']['network']['bytesIn'] - network_bytesIn) / timeint
        datav['network_bytesOut'] = (alldata['serverStatus']['network']['bytesOut'] - network_bytesOut) / timeint
        datav['opcounters_command'] = (alldata['serverStatus']['opcounters']['command'] - opcounters_command) / timeint
        datav['opcounters_delete'] = (alldata['serverStatus']['opcounters']['delete'] - opcounters_delete) / timeint
        datav['opcounters_getmore'] = (alldata['serverStatus']['opcounters']['getmore'] - opcounters_getmore) / timeint
        datav['opcounters_insert'] = (alldata['serverStatus']['opcounters']['insert'] - opcounters_insert) / timeint
        datav['opcounters_query'] = (alldata['serverStatus']['opcounters']['query'] - opcounters_query) / timeint
        datav['opcounters_update'] = (alldata['serverStatus']['opcounters']['update'] - opcounters_update) / timeint
    except:
        datav = {}
    c.close()
    statlist['status'] = datav
    return statlist


# print check_mongo('http://localhost:27017/_status')

## memcache 應用狀態,間隔時間為誒60s
def server_stat(hlist):
    data = {}
    if not os.path.exists('/usr/bin/nc'):
        os.popen("yum -y install nc >> /dev/null")
    result = commands.getoutput('nc -z -w 1 %s %s' % (hlist[0], hlist[1]))
    if 'succeeded' in result:
        data['memcache_stat'] = 1
    else:
        data['memcache_stat'] = 0
    return data


def my_telnet(hlist):
    try:
        tn = telnetlib.Telnet(hlist[0], hlist[1])
        tn.read_very_eager()
        tn.write('stats' + '\n')
        result = tn.read_until('END').replace('\r', '').split('\n')
        result = result[1:-1]
    except:
        result = {}
    return result


def check_memcache(hlist):
    '''
    :param hlist: ['localhost','11211']
    :return:
    '''
    stat = {}
    mstat = {}
    statlist = {}
    timeint = 60
    listvalue = ['version', 'uptime', 'curr_connections', 'total_connections', 'auth_cmds', 'auth_errors', 'bytes',
                 'limit_maxbytes', 'bytes_read', 'bytes_written', 'cas_badval', 'cas_hits', 'cas_misses', 'decr_hits',
                 'decr_misses', 'delete_hits', 'delete_misses', 'get_hits', 'get_misses', 'incr_hits', 'incr_misses',
                 'cmd_flush', 'cmd_get', 'cmd_set', 'curr_items', 'total_items', 'evictions', 'threads']
    listslip = ['total_connections', 'auth_cmds', 'auth_errors', 'bytes_read', 'bytes_written', 'cas_badval',
                'cas_hits', 'cas_misses', 'decr_hits', 'decr_misses', 'delete_hits', 'delete_misses', 'get_hits',
                'get_misses', 'incr_hits', 'incr_misses', 'cmd_flush', 'cmd_get', 'cmd_set', 'total_items',
                'evictions', ]
    try:
        result = my_telnet(hlist)
        for row in result:
            if row.split()[1] in listvalue:
                stat[row.split()[1]] = row.split()[2]
    except:
        stat = {}
    time.sleep(timeint)
    try:
        result = my_telnet(hlist)
        for row in result:
            if row.split()[1] in listslip:
                mstat[row.split()[1]] = (int(row.split()[2]) - int(stat[row.split()[1]])) / timeint
            elif row.split()[1] == 'uptime' or row.split()[1] == 'version':
                mstat[row.split()[1]] = row.split()[2]
    except:
        mstat = {}
    stat_p = dict(server_stat(hlist).items() + mstat.items())
    statlist['status'] = stat_p
    return statlist


# print check_memcache(['localhost','11211'])


# mysql_master應用狀態
###### mysql-master #####
def get_curl(conn):
    data = {}
    try:
        cur = conn.cursor()
        data['mysql_status'] = 1
    except:
        data['mysql_status'] = 0
    return data


def get_mysql_ver(cur):
    datav = {}
    sql = "select version()"
    try:
        cur.execute(sql)
        datav['mysql_ver'] = cur.fetchone()[0]
    except:
        datav['mysql_ver'] = 'err'
    return datav


'''
Uptime:在綫時間，Com_insert：每秒查詢，Com_delete：每秒刪除，Com_update：每秒更新，Com_rollback：每秒回滾，Com_commit：每秒更新，Com_begin：每秒begin，Questions：每秒請求，Slow_queries：緩慢請求，Bytes_sent：每秒發送字節，Bytes_received：每秒接受字節，Created_tmp_disk_tables：臨時磁盤表,Created_tmp_files:臨時文件,Created_tmp_tables:臨時表,Threads_connected:當前連接
'''


def get_mysql_status(cur):
    timeint = 60
    namelist = ['Uptime', 'Com_insert', 'Com_delete', 'Com_select', 'Com_update', 'Com_rollback', 'Com_commit',
                'Com_begin', 'Questions', 'Slow_queries', 'Bytes_sent', 'Bytes_received', 'Created_tmp_disk_tables',
                'Created_tmp_files', 'Created_tmp_tables', 'Threads_connected']
    datav = {}
    sql = "show global status"
    try:
        cur.execute(sql)
        for line in cur.fetchall():
            if line[0] in namelist: datav[line[0]] = line[1]
        time.sleep(timeint)
        cur.execute(sql)
        for line in cur.fetchall():
            if line[0] == 'Threads_connected':
                datav[line[0]] = int(line[1])
            elif line[0] in namelist:
                datav[line[0]] = (int(line[1]) - int(datav[line[0]])) / timeint
    except:
        datav['mysql_up'] = 'err'
    return datav


def get_mysql_hit(cur):
    datav = {}
    sql_1 = "show global status like 'Qcache_inserts'"
    sql_2 = "show status like 'Qcache_hits'"
    cur.execute(sql_1)
    tmp = cur.fetchone()
    Qcache_inserts = int(tmp[1])
    cur.execute(sql_2)
    tmp = cur.fetchone()
    Qcache_hits = int(tmp[1])
    if (Qcache_inserts + Qcache_hits) != 0:
        Query_cache_hits = Qcache_hits * 100 / (Qcache_inserts + Qcache_hits)
    else:
        Query_cache_hits = 0
    datav['Query_cache_hits'] = Query_cache_hits
    sql_1 = "show global status like 'Innodb_buffer_pool_reads'"
    sql_2 = "show global status like 'Innodb_buffer_pool_read_requests'"
    try:
        tmp = cur.fetchone()
        Innodb_buffer_pool_reads = int(tmp[1])
        cur.execute(sql_2)
        tmp = cur.fetchone()
        Innodb_buffer_pool_read_requests = int(tmp[1])
        Innodb_buffer_hits = (1 - Innodb_buffer_pool_reads / Innodb_buffer_pool_read_requests) * 100
        datav['Innodb_buffer_hits'] = Innodb_buffer_hits
    except:
        datav['Innodb_buffer_hits'] = 0
    return datav


def check_mysql(hostname, username, password, sport=3306, socket='/tmp/mysql.sock'):
    stat = {}
    conn = pymysql.connect(host=hostname, user=username, passwd=password, port=sport, unix_socket=socket)
    try:
        mysql_s = get_curl(conn)
        cur = conn.cursor()
        version = get_mysql_ver(cur)
        status = get_mysql_status(cur)
        hit = get_mysql_hit(cur)
        statlist = dict(mysql_s.items() + version.items() + status.items() + hit.items())
    except:
        statlist = {}
    stat['status'] = statlist
    return stat


# print check_mysql('localhost', 'root', 'qwe123',3306,'/var/run/mysqld/mysqld.sock')
# {'status': {'Com_select': 3, 'Uptime': 1, 'Com_commit': 2, 'Com_insert': 0, 'Query_cache_hits': 0, 'Created_tmp_tables': 0, 'Threads_connected': 18, 'Bytes_sent': 2761, 'Com_update': 0, 'Com_begin': 2, 'Com_delete': 0, 'Created_tmp_disk_tables': 0, 'mysql_status': 1, 'Questions': 8, 'Created_tmp_files': 0, 'Innodb_buffer_hits': 0, 'Bytes_received': 874, 'Slow_queries': 0, 'mysql_ver': '5.7.27-0ubuntu0.18.04.1', 'Com_rollback': 0}}

# mysql_slave應用狀態
def get_slave_curl(conn):
    data = {}
    #	conn = pymysql.connect(host='localhost',user='root',passwd='',port=3306,unix_socket='/tmp/mysql.sock')
    try:
        cur = conn.cursor()
        data['mysql_status'] = 1
    except:
        data['mysql_status'] = 0
    return data


def get_slave_status(cur):
    datav = {}
    try:
        sql = "show slave status"
        cur.execute(sql)
        index = cur.description
        res = cur.fetchone()
        if res is not None:
            for i in range(len(index) - 1):
                datav[index[i][0]] = res[i]
        else:
            datav = {}
    except:
        datav = {}
    return datav


def check_mysql_slave(hostname, username, password, sport=3306, socket='/tmp/mysql.sock'):
    statlist = {}
    stat = {}
    conn = pymysql.connect(host=hostname, user=username, passwd=password, port=sport, unix_socket=socket)
    try:
        mysql_s = get_slave_curl(conn)
        cur = conn.cursor()
        status = get_slave_status(cur)
        statlist = dict(mysql_s.items() + status.items())
    except:
        statlist = {}
    stat['status'] = statlist
    return stat


# print check_mysql_slave('localhost', 'root', 'EfUn!@%32*&',3306,'/var/lib/mysql/mysql.sock')
# {'status': {u'Replicate_Wild_Do_Table': '', u'Master_SSL_CA_Path': '', u'Last_Error': '', u'Until_Log_File': '', u'Seconds_Behind_Master': 0, 'mysql_status': 1, u'Master_Port': 3306, u'Until_Log_Pos': 0, u'Master_Log_File': 'mysql-bin.004422', u'Read_Master_Log_Pos': 303827812, u'Replicate_Do_DB': '', u'Master_SSL_Verify_Server_Cert': 'No', u'Exec_Master_Log_Pos': 303827812, u'Replicate_Ignore_Table': '', u'Replicate_Do_Table': '', u'Relay_Master_Log_File': 'mysql-bin.004422', u'Master_SSL_Allowed': 'No', u'Master_SSL_CA_File': '', u'Slave_IO_State': 'Waiting for master to send event', u'Relay_Log_File': 'mysqld-relay-bin.001219', u'Replicate_Ignore_DB': '', u'Last_IO_Error': '', u'Until_Condition': 'None', u'Relay_Log_Space': 303828156, u'Last_Errno': 0, u'Master_Host': '10.20.35.114', u'Master_SSL_Key': '', u'Skip_Counter': 0, u'Slave_SQL_Running': 'Yes', u'Relay_Log_Pos': 303827957, u'Master_SSL_Cert': '', u'Last_IO_Errno': 0, u'Slave_IO_Running': 'Yes', u'Connect_Retry': 60, u'Last_SQL_Errno': 0, u'Replicate_Wild_Ignore_Table': '', u'Master_User': 'efunsync', u'Master_SSL_Cipher': ''}}


def check_resin():
    pass


def check_tomcat():
    pass


def check_elasticsearch():
    url = 'http://127.0.0.1:9200/_nodes/stats/jvm,os,process,thread_pool'
    timeint = 60
    stat = {}
    statlist = {}
    c, html = mypycurl(url)
    try:
        c.perform()
        # print html.getvalue()
        alldata = loads(html.getvalue())
        print alldata
        accept_conn = alldata['accepted conn']
    except:
        return 0
    time.sleep(timeint)
    c, html = mypycurl(url)
    try:
        c.perform()
        alldata = loads(html.getvalue())
        process_manager = alldata['process manager']
        uptime = alldata['start since']
        if 'accept_conn' in dir():
            accept_conn = round(abs(int(alldata['accepted conn']) - int(accept_conn) / timeint), 2)
        else:
            accept_conn = alldata['accepted conn']
        stat['accept_conn'] = accept_conn
        stat['listen_queue'] = alldata['listen queue']
        stat['max_listen_queue'] = alldata['max listen queue']
        stat['active_processes'] = alldata['active processes']
        stat['total_processes'] = alldata['total processes']
        stat['max_active_processes'] = alldata['max active processes']
        stat['max_children_reached'] = alldata['max children reached']
        stat['http_code'] = c.getinfo(pycurl.HTTP_CODE)
        stat['http_total_time'] = c.getinfo(pycurl.TOTAL_TIME)
    except:
        stat = {}
    c.close()
    statlist['status'] = stat
    return statlist


# check_elasticsearch()

def check_rocketmq():
    pass


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


def main():
    if sys.argv[1] == 'jvm':
        func = check_jvm(sys.argv[2])
    elif sys.argv[1] == 'dns':
        func = check_dns()
    elif sys.argv[1] == 'rsync':
        func = check_rsync(sys.argv[2])
    elif sys.argv[1] == 'ssh':
        func = check_ssh()
    elif sys.argv[1] == 'vsftpd':
        func = check_vsftpd(sys.argv[2])
    elif sys.argv[1] == 'nginx':
        func = check_nginx(sys.argv[2])
    elif sys.argv[1] == 'php':
        func = check_php(sys.argv[2])
    elif sys.argv[1] == 'memcache':
        func = check_memcache(sys.argv[2])
    elif sys.argv[1] == 'mongo':
        func = check_mongo(sys.argv[2])
    elif sys.argv[1] == 'mycat':
        func = check_mycat(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
    elif sys.argv[1] == 'mysql':
        if sys.argv[6] and sys.argv[5]:
            func = check_mysql(sys.argv[2], sys.argv[3], sys.argv[4], int(sys.argv[5]), sys.argv[6])
        elif not sys.argv[6] and sys.argv[5]:
            func = check_mysql(sys.argv[2], sys.argv[3], sys.argv[4], int(sys.argv[5]))
        elif not sys.argv[6] and not sys.argv[5]:
            func = check_mysql(sys.argv[2], sys.argv[3], sys.argv[4])
    elif sys.argv[1] == 'mysql_slave':
        if sys.argv[6] and sys.argv[5]:
            func = check_mysql_slave(sys.argv[2], sys.argv[3], sys.argv[4], int(sys.argv[5]), sys.argv[6])
        elif not sys.argv[6] and sys.argv[5]:
            func = check_mysql_slave(sys.argv[2], sys.argv[3], sys.argv[4], int(sys.argv[5]))
        elif not sys.argv[6] and not sys.argv[5]:
            func = check_mysql_slave(sys.argv[2], sys.argv[3], sys.argv[4])
    elif sys.argv[1] == 'redis':
        func = check_redis(sys.argv[2])
    elif sys.argv[1] == 'keepalived':
        func = check_keepalived()
    elif sys.argv[1] == 'lvs':
        func = check_lvs()
    elif sys.argv[1] == 'haproxy':
        func = check_haproxy()
    return make_json(func)

# if __name__ == '__main__':
#     print main()

# print check_mysql('localhost', 'root', 'qwe123',3306, '/var/run/mysqld/mysqld.sock')
