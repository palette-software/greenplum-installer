#!/bin/sh

# Example usage:
#     ./build.sh /tmp/greenplum-install-4.3.7.3 4.3.7.3

set -e

# Check arg count
if [ "$#" -ne 2 ]; then
  echo "Usage: $0 <GREENPLUM_BINARY_PATH> <VERSION>"
  exit 1
fi

GP_BINARY_PATH=$1
#GP_VERSION=4.3.7.3
GP_VERSION=$2


GP_BUILD=2
GP_ARCH=x86_64
GP_BASENAME=greenplum-db-${GP_VERSION}-build-${GP_BUILD}-RHEL5-${GP_ARCH}
GP_BIN=${GP_BASENAME}.bin
GP_DIRNAME=/greenplum-db

GP_PREFIX=/usr/local

GP_INSTALLED_PATH=${GP_PREFIX}${GP_DIRNAME}

RPM_ROOT=/tmp/gp-rpm-build
RPM_BUILD_ROOT=${RPM_ROOT}/root
RPM_OUT_PATH=${RPM_ROOT}/_build
RPM_GP_PATH=${RPM_BUILD_ROOT}${GP_INSTALLED_PATH}

GP_BIN_FULLPATH=${GP_BINARY_PATH}/${GP_BIN}

# Create the root directory & the greenplum directory
mkdir -p ${RPM_BUILD_ROOT}
mkdir -p ${RPM_GP_PATH}

mkdir -p ${RPM_OUT_PATH}

# Create the gpadmin home directory and add needed files
mkdir -p ${RPM_BUILD_ROOT}/home/gpadmin
cp gpinitsystem_singlenode ${RPM_BUILD_ROOT}/home/gpadmin/
cp gp_vmem_protect_limit.sh ${RPM_BUILD_ROOT}/home/gpadmin/

# Make greenplum a service
mkdir -p ${RPM_BUILD_ROOT}/etc/init.d/
cp greenplum.init.d ${RPM_BUILD_ROOT}/etc/init.d/greenplum

# extract the gp tarball
SKIP=`awk '/^__END_HEADER__/ {print NR + 1; exit 0; }' "${GP_BIN_FULLPATH}"`
echo "+ Extracting from ${GP_BIN_FULLPATH} to ${RPM_GP_PATH}, skipping ${SKIP} bytes"
tail -n +${SKIP} "${GP_BIN_FULLPATH}" | tar xzf - -C ${RPM_GP_PATH}

# replace the GPHOME env variable
echo "+ Replacing GPHOME to ${GP_INSTALLED_PATH} in greenplum_path.sh"
sed "s,^GPHOME.*,GPHOME=${GP_INSTALLED_PATH}," ${RPM_GP_PATH}/greenplum_path.sh > ${RPM_GP_PATH}/greenplum_path.sh.tmp
mv ${RPM_GP_PATH}/greenplum_path.sh.tmp ${RPM_GP_PATH}/greenplum_path.sh

echo "--> New greenplum_path.sh is:"
cat ${RPM_GP_PATH}/greenplum_path.sh

rpmbuild -bb --buildroot ${RPM_BUILD_ROOT} \
  --define "version ${GP_VERSION}" \
  --define "buildrelease ${GP_BUILD}" \
  --define "_rpmdir ${RPM_OUT_PATH}" \
  greenplum-metal.spec

# clean the rpm directory
rm -rf ${RPM_BUILD_ROOT}
