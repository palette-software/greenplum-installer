%define serviceuser gpadmin
%define servicehome /home/gpadmin

#   Disable any prep shell actions. replace them with simply 'true'
# %define __spec_prep_post true
# %define __spec_prep_pre true
#   Disable any build shell actions. replace them with simply 'true'
# %define __spec_build_post true
# %define __spec_build_pre true
#   Disable any install shell actions. replace them with simply 'true'
# %define __spec_install_post true
# %define __spec_install_pre true
#   Disable any clean shell actions. replace them with simply 'true'
# %define __spec_clean_post true
# %define __spec_clean_pre true
# Disable checking for unpackaged files ?
#%undefine __check_files

# Use md5 file digest method.
# The first macro is the one used in RPM v4.9.1.1
%define _binary_filedigest_algorithm 1
# This is the macro I find on OSX when Homebrew provides rpmbuild (rpm v5.4.14)
%define _build_binary_file_digest_algo 1

# Use bzip2 payload compression
%define _binary_payload w9.bzdio


Name: palette-greenplum-installer
Version: %version
Epoch: 0
Release: %buildrelease
Summary: Greenplum Database
AutoReqProv: no
# Seems specifying BuildRoot is required on older rpmbuild (like on CentOS 5)
# fpm passes '--define buildroot ...' on the commandline, so just reuse that.
#BuildRoot: %buildroot
# Add prefix, must not end with /

Prefix: /

Group: default
License: Apache2
Vendor: Palette Software
URL: http://www.palette-software.com
Packager: Palette Developers <developers@palette-software.com>

# Sed will be required for GP 4.3.10 and up instead of ed
Requires: initscripts >= 9.03.53
Requires: gcc, python, python-pip, python-paramiko, net-tools, python-devel, ed, python-PSI, python-lockfile, perl
Requires: kernel < 3.10, kernel >= 2.6.32-431

# Add the user for the service & setup SELinux
# ============================================

#Requires(pre): /usr/sbin/useradd, /usr/bin/getent
#Requires(postun): /usr/sbin/userdel

%pre
# Make sure that /data is mounted
if [ ! -d "/data" ]; then
    echo "Installation requires a mount on /data !"
    exit 1
fi

export DATA_MOUNT_INFO=`df -T | grep /data | tr -s ' '`
export FS_TYPE=`echo $DATA_MOUNT_INFO  | cut -d' ' -f2`
export TOTAL_SIZE=`echo $DATA_MOUNT_INFO  | cut -d' ' -f3`

# Make sure that /data is formatted as xfs
if [ "Xxfs" != "X$FS_TYPE" ]; then
    echo "Disk mounted to /data must be formatted as xfs!"
    exit 1
fi

# Make sure /data is at least 1 TB
if [ "$TOTAL_SIZE" -lt "1048062980" ]; then
    echo "Disk mounted to /data must be at least 1 TB!"
    exit 1
fi

# Add the user and set its home and limits
/usr/bin/getent passwd %{serviceuser} || /usr/sbin/useradd %{serviceuser}
# /usr/bin/getent group %{serviceuser} || /usr/sbin/groupadd -g %{serviceuser}

# Limit settings according to Pivotal Greenplum Install Guide recommendations
echo "gpadmin soft nofile 65536" > /etc/security/limits.d/99-gpadmin-limits.conf
echo "gpadmin hard nofile 65536" >> /etc/security/limits.d/99-gpadmin-limits.conf
echo "gpadmin soft nproc 131072" >> /etc/security/limits.d/99-gpadmin-limits.conf
echo "gpadmin hard nproc 131072" >> /etc/security/limits.d/99-gpadmin-limits.conf

# Systctl settings according to Pivotal Greenplum Install Guide recommendations
# The append is missing from the first line intentionally
echo "kernel.shmmax = 500000000" | sudo tee /etc/sysctl.d/90-gpadmin.conf
echo "kernel.shmmni = 4096" | sudo tee --append /etc/sysctl.d/90-gpadmin.conf
echo "kernel.shmall = 4000000000" | sudo tee --append /etc/sysctl.d/90-gpadmin.conf
echo "kernel.sem = 250 512000 100 2048" | sudo tee --append /etc/sysctl.d/90-gpadmin.conf
echo "kernel.sysrq = 1" | sudo tee --append /etc/sysctl.d/90-gpadmin.conf
echo "kernel.core_uses_pid = 1" | sudo tee --append /etc/sysctl.d/90-gpadmin.conf
echo "kernel.msgmnb = 65536" | sudo tee --append /etc/sysctl.d/90-gpadmin.conf
echo "kernel.msgmax = 65536" | sudo tee --append /etc/sysctl.d/90-gpadmin.conf
echo "kernel.msgmni = 2048" | sudo tee --append /etc/sysctl.d/90-gpadmin.conf
echo "net.ipv4.tcp_syncookies = 1" | sudo tee --append /etc/sysctl.d/90-gpadmin.conf
echo "net.ipv4.ip_forward = 0" | sudo tee --append /etc/sysctl.d/90-gpadmin.conf
echo "net.ipv4.conf.default.accept_source_route = 0" | sudo tee --append /etc/sysctl.d/90-gpadmin.conf
echo "net.ipv4.tcp_tw_recycle = 1" | sudo tee --append /etc/sysctl.d/90-gpadmin.conf
echo "net.ipv4.tcp_max_syn_backlog = 4096" | sudo tee --append /etc/sysctl.d/90-gpadmin.conf
echo "net.ipv4.conf.all.arp_filter = 1" | sudo tee --append /etc/sysctl.d/90-gpadmin.conf
echo "net.ipv4.ip_local_port_range = 1025 65535" | sudo tee --append /etc/sysctl.d/90-gpadmin.conf
echo "net.core.netdev_max_backlog = 10000" | sudo tee --append /etc/sysctl.d/90-gpadmin.conf
echo "net.core.rmem_max = 2097152" | sudo tee --append /etc/sysctl.d/90-gpadmin.conf
echo "net.core.wmem_max = 2097152" | sudo tee --append /etc/sysctl.d/90-gpadmin.conf
echo "vm.overcommit_memory = 2" | sudo tee --append /etc/sysctl.d/90-gpadmin.conf
echo "vm.overcommit_ratio = 95" | sudo tee --append /etc/sysctl.d/90-gpadmin.conf
sudo sysctl --system

# Set blocksize
DISKS=`sudo lsblk -o name,type -P -e 1 | grep -e "TYPE=\"part\"" | cut -d' ' -f1`
REGEX="NAME=\"(.*)\""
for f in $DISKS
    do
    if [[ $f =~ $REGEX ]]
    then
        name="${BASH_REMATCH[1]}"
        /sbin/blockdev --setra 16384 /dev/$name
    fi
done

# Disable Transparent Huge Pages
LINE="echo never > /sys/kernel/mm/redhat_transparent_hugepage/enabled"
FILE=/etc/rc.d/rc.local
sudo grep -q "$LINE" "$FILE" || echo "$LINE" | sudo tee --append "$FILE"

# Override the SELinux flag that disallows httpd to connect to the go process
# https://stackoverflow.com/questions/23948527/13-permission-denied-while-connecting-to-upstreamnginx
setsebool httpd_can_network_connect on -P

%postun
# Dont remove the user

# TODO: we should switch back the httpd_can_network_connect flag for SELinux, IF we know that its safe to do so


# Generic RPM parts
# =================

%description
Greenplum Database is an advanced, fully featured, open source data warehouse. It provides powerful and rapid analytics on petabyte scale data volumes. Uniquely geared toward big data analytics, Greenplum Database is powered by the world’s most advanced cost-based query optimizer delivering high analytical query performance on large data volumes.

%prep
# noop

%build
# noop

%install
# Create the gpadmin home directory and add needed files
mkdir -p %{buildroot}/home/gpadmin/.ssh
cp gpinitsystem_singlenode %{buildroot}/home/gpadmin/
cp gp_vmem_protect_limit.sh %{buildroot}/home/gpadmin/
touch %{buildroot}/home/gpadmin/.ssh/authorized_keys

# Make greenplum a service
mkdir -p %{buildroot}/etc/init.d/
cp greenplum.init.d %{buildroot}/etc/init.d/greenplum

%clean
# noop

%post
source /usr/local/greenplum-db/greenplum_path.sh
sudo mkdir -m 755 -p /data/primary
sudo chown gpadmin:gpadmin /data/primary
sudo mkdir -m 755 -p /data/master
sudo chown gpadmin:gpadmin /data/master
sudo mkdir -m 755 -p /var/log/greenplum
sudo chown gpadmin:gpadmin /var/log/greenplum

echo "127.0.0.1" | sudo tee /etc/gphosts

# Patch bashrc of gpadmin
FILE=/home/gpadmin/.bashrc
LINE="source /usr/local/greenplum-db/greenplum_path.sh"
sudo grep -q "$LINE" "$FILE" || echo "$LINE" | sudo tee --append "$FILE"
LINE="export MASTER_DATA_DIRECTORY=/data/master/gpsne-1"
sudo grep -q "$LINE" "$FILE" || echo "$LINE" | sudo tee --append "$FILE"

sudo -i -u gpadmin gpssh-exkeys -f /etc/gphosts
sudo -i -u gpadmin gpinitsystem -a -h /etc/gphosts -c /home/gpadmin/gpinitsystem_singlenode

# Tune some greenplum configuration
export VMEM_PROTECT_LIMIT=`/home/gpadmin/gp_vmem_protect_limit.sh 4 0`
sudo -i -u gpadmin gpconfig -c gp_vmem_protect_limit -v $VMEM_PROTECT_LIMIT
sudo -i -u gpadmin gpconfig -c statement_mem -v 1000MB

# Decorate pg_hba.conf for enabling remote and local access
FILE=/data/master/gpsne-1/pg_hba.conf
LINE="local all all trust"
sudo grep -q "$LINE" "$FILE" || echo "$LINE" | sudo tee --append "$FILE"
LINE="host all all 0.0.0.0/0 md5"
sudo grep -q "$LINE" "$FILE" || echo "$LINE" | sudo tee --append "$FILE"
LINE="hostssl all all 0.0.0.0/0 md5"
sudo grep -q "$LINE" "$FILE" || echo "$LINE" | sudo tee --append "$FILE"
LINE="host all all ::1/128 trust"
sudo grep -q "$LINE" "$FILE" || echo "$LINE" | sudo tee --append "$FILE"

# Make greenplum a service
sudo chkconfig --add greenplum

%files
%defattr(-,gpadmin,gpadmin,-)

/usr/local/greenplum-db
%attr(755, root, root) /etc/init.d/greenplum
%attr(700, -, -) %dir /home/gpadmin
%attr(700, -, -) /home/gpadmin/gpinitsystem_singlenode
%attr(700, -, -) /home/gpadmin/gp_vmem_protect_limit.sh
%attr(700, -, -) %dir /home/gpadmin/.ssh
%attr(600, -, -) %config(noreplace) /home/gpadmin/.ssh/authorized_keys

%changelog

