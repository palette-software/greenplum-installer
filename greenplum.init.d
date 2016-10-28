#!/bin/sh

### BEGIN INIT INFO
# Provides:          greenplum
# Required-Start:    $network $local_fs $remote_fs $syslog sshd
# Required-Stop:     $network $local_fs $remote_fs $syslog sshd
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Start greenplum daemons at boot time
# Description:       Enable greenplum service.
### END INIT INFO

# Run the greenplum path script script
. /usr/local/greenplum-db/greenplum_path.sh

# Who to run the postmaster as, usually "postgres".  (NOT "root")
GPUSER=gpadmin
GPLOG="/var/log/greenplum/service.log"
export MASTER_DATA_DIRECTORY=/data/master/gpsne-1

set -e


# Parse command line parameters.
case $1 in
  start)
    echo -n "Starting Greenplum RDMS: "
    su -l gpadmin -c "gpstart -a" >>$GPLOG 2>&1
    echo "ok"
    ;;
  stop)
    echo -n "Stopping Greenplum RDMS: "
    su -l gpadmin -c "gpstop -a -M fast" >>$GPLOG 2>&1
    echo "ok"
    ;;
  restart)
    echo -n "Restarting Greenplum RDMS: "
    su -l gpadmin -c "gpstop -a -M fast -r" >>$GPLOG 2>&1
    echo "ok"
    ;;
  reload)
    echo -n "Reload Greenplum RDMS: "
    su -l gpadmin -c "gpstop -u" >>$GPLOG 2>&1
    echo "ok"
    ;;
  status)
    su -l gpadmin -c "gpstate"
    ;;
  *)
    # Print help
    echo "Usage: $0 {start|stop|restart|reload|status}" 1>&2
    exit 1
    ;;
esac

exit 0
