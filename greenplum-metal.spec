%define serviceuser gpadmin
%define servicehome /var/lib/gpadmin

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
License: GNU GPL v3
Vendor: Palette Software
URL: http://www.palette-software.com
Packager: Palette Developers <developers@palette-software.com>

# Sed will be required for GP 4.3.10 and up instead of ed
Requires: initscripts >= 9.03.53
Requires: gcc, python, python-pip, python-paramiko, net-tools, python-devel, ed, python-lockfile, perl
# All RHEL 7 and CentOS 7 versions use kernel version 3.10.x, but only 7.3+ versions are supported by Greenplum
# Requires: kernel < 3.10, kernel >= 2.6.32-431

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

# The requirement is turned OFF by default

CHECK_DATA_PARTITION=0
if [ -n "$PALETTE_CHECK_DATA_PARTITION" ]; then
    CHECK_DATA_PARTITION=$PALETTE_CHECK_DATA_PARTITION
fi

if [ "$CHECK_DATA_PARTITION" -ne "0" ]; then
    export DATA_MOUNT_INFO=`df -T | grep /data | tr -s ' '`
    export FS_TYPE=`echo $DATA_MOUNT_INFO  | cut -d' ' -f2`
    export TOTAL_SIZE=`echo $DATA_MOUNT_INFO  | cut -d' ' -f3`

    # Make sure that /data is formatted as xfs
    if [ "Xxfs" != "X$FS_TYPE" ]; then
        echo "Disk mounted to /data must be formatted as xfs!"
        exit 1
    fi

    # The default requirement is 1 TB
    REQUIRED_DATA_PARTITION_SIZE=1048062980
    if [ -n "$PALETTE_REQUIRED_DATA_PARTITION_SIZE" ]; then
    REQUIRED_DATA_PARTITION_SIZE=$PALETTE_REQUIRED_DATA_PARTITION_SIZE
    fi

    # Make sure /data is at least the required size
    if [ "$TOTAL_SIZE" -lt "$REQUIRED_DATA_PARTITION_SIZE" ]; then
        echo "Disk mounted to /data must be at least $REQUIRED_DATA_PARTITION_SIZE KB!"
        exit 1
    fi
fi

# Add the user and set its home and limits
/usr/bin/getent passwd %{serviceuser} || /usr/sbin/useradd -d %{servicehome} %{serviceuser}
# /usr/bin/getent group %{serviceuser} || /usr/sbin/groupadd -g %{serviceuser}

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
#
setsebool httpd_can_network_connect on -P || true

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
# Copy gpadmin home directory and needed files
cp -a var %{buildroot}

# Copy configuration files
cp -a etc %{buildroot}

%clean
rm -rf %{buildroot}

%post
# Apply the sysctl settings (/etc/sysctl.d/90-gpadmin.conf) without machine restart
sudo sysctl --system

source /usr/local/greenplum-db/greenplum_path.sh
sudo mkdir -m 755 -p /data/primary
sudo chown gpadmin:gpadmin /data/primary
sudo mkdir -m 755 -p /data/master
sudo chown gpadmin:gpadmin /data/master
sudo mkdir -m 755 -p /var/log/greenplum
sudo chown gpadmin:gpadmin /var/log/greenplum

# Patch bashrc of gpadmin
FILE=%{servicehome}/.bashrc
LINE="source /usr/local/greenplum-db/greenplum_path.sh"
sudo grep -q "$LINE" "$FILE" || echo "$LINE" | sudo tee --append "$FILE"
LINE="export MASTER_DATA_DIRECTORY=/data/master/gpsne-1"
sudo grep -q "$LINE" "$FILE" || echo "$LINE" | sudo tee --append "$FILE"

sudo -i -u gpadmin gpssh-exkeys -f /etc/gphosts
sudo -i -u gpadmin gpinitsystem -a -h /etc/gphosts -c %{servicehome}/gpinitsystem_singlenode

# Tune some greenplum configuration
export VMEM_PROTECT_LIMIT=`%{servicehome}/gp_vmem_protect_limit.sh 4 0`
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

# Enable postgres port on firewall
sudo lokkit -p 5432:tcp

# Make greenplum a service
sudo chkconfig --add greenplum

service greenplum restart

%files
%defattr(-,gpadmin,gpadmin,-)

/usr/local/greenplum-db
%attr(755, root, root) /etc/init.d/greenplum
# Sysctl settings according to Pivotal Greenplum Install Guide recommendations
%attr(644, root, root) /etc/sysctl.d/90-gpadmin.conf
# Limit settings according to Pivotal Greenplum Install Guide recommendations
%attr(644, root, root) /etc/security/limits.d/99-gpadmin-limits.conf
# Localhost (127.0.0.1)
%attr(644, root, root) /etc/gphosts

%attr(700, -, -) %dir %{servicehome}
%attr(700, -, -) %{servicehome}/gpinitsystem_singlenode
%attr(700, -, -) %{servicehome}/gp_vmem_protect_limit.sh
%attr(700, -, -) %dir %{servicehome}/.ssh
%attr(600, -, -) %config(noreplace) %{servicehome}/.ssh/authorized_keys


%changelog
