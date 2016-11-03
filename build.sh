#!/bin/sh

set -e

# Have a full path to the official Greenplum installer, that we are going to wrap
export GREENPLUM_BINARY_FILE="$(ls greenplum-db-*x86_64.bin)"
export GREENPLUM_BINARY_PATH="${GREENPLUM_BINARY_FILE}"
# Extract the Greenplum version number from the name of the binary file
export GREENPLUM_VERSION="$(echo "$GREENPLUM_BINARY_FILE" | awk -F"-" '{ print $3 }')"

if [ -z "$TRAVIS_BUILD_NUMBER" ]; then echo "TRAVIS_BUILD_NUMBER environment variable is not set!"; exit 1; fi

# The build number is coming from Travis
PACKAGE_VERSION=${TRAVIS_BUILD_NUMBER}
GP_DIRNAME=/greenplum-db
GP_PREFIX=/usr/local

GP_INSTALL_PATH=${GP_PREFIX}${GP_DIRNAME}

RPM_ROOT=/tmp/gp-rpm-build
RPM_BUILD_ROOT=${RPM_ROOT}/root
RPM_OUT_PATH=${RPM_ROOT}/_build
RPM_GP_PATH=${RPM_BUILD_ROOT}${GP_INSTALL_PATH}

# Create the root directory & the greenplum directory
mkdir -p ${RPM_BUILD_ROOT}
mkdir -p ${RPM_GP_PATH}

mkdir -p ${RPM_OUT_PATH}

# extract the gp tarball
SKIP=$(awk '/^__END_HEADER__/ {print NR + 1; exit 0; }' "${GREENPLUM_BINARY_PATH}")
echo "+ Extracting from ${GREENPLUM_BINARY_PATH} to ${RPM_GP_PATH}, skipping ${SKIP} bytes"
tail -n +"${SKIP}" "${GREENPLUM_BINARY_PATH}" | tar xzf - -C ${RPM_GP_PATH}

# replace the GPHOME env variable
echo "+ Replacing GPHOME to ${GP_INSTALL_PATH} in greenplum_path.sh"
sed "s,^GPHOME.*,GPHOME=${GP_INSTALL_PATH}," ${RPM_GP_PATH}/greenplum_path.sh > ${RPM_GP_PATH}/greenplum_path.sh.tmp
mv ${RPM_GP_PATH}/greenplum_path.sh.tmp ${RPM_GP_PATH}/greenplum_path.sh

echo "--> New greenplum_path.sh is:"
cat ${RPM_GP_PATH}/greenplum_path.sh

rpmbuild -bb --buildroot ${RPM_BUILD_ROOT} \
  --define "version ${GREENPLUM_VERSION}" \
  --define "buildrelease ${PACKAGE_VERSION}" \
  --define "_rpmdir ${RPM_OUT_PATH}" \
  greenplum-metal.spec

# clean the rpm directory
rm -rf ${RPM_BUILD_ROOT}
