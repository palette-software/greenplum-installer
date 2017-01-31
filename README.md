# Palette Insight Architecture

![Palette Insight Architecture](https://github.com/palette-software/palette-insight/blob/master/insight-system-diagram.png?raw=true)

# Palette Greenplum Installer
[Greenplum Database]:  http://greenplum.org

## IMPORTANT NOTE

This repo uses [Git Large File Storage](https://git-lfs.github.com/). This means you need to install it in order to clone all the files of this repo successfully.

## What is Palette Greenplum Installer?

The purpose of this repository to ease the installation of the [Greenplum Database]
by providing a RPM package.

## How do I set up Palette Greenplum Installer?

### Packaging

To build the package you may use the [build.sh](build.sh):

```bash
export TRAVIS_BUILD_NUMBER=123
./build.sh
```

The repository contains the version greenplum-db-4.3.7.3-build-2-RHEL5-x86_64 but
supports others too.

### Installation

Install it using either yum or rpm.

**NOTE** The [Greenplum Shell](https://github.com/palette-software/insight-deploy/tree/master#greenplum-shell)
Ansible Playbook can be used to provision a computer before the RPM can be installed.

The following process is executed by the installer:

- checks the `/data` directory (this will be used to store the database storage):
  - it should exist
  - a disk should be mounted with 1 TB of free diskspace
  - it should be formated with `XFS` filesystem
- creates the `gpadmin` user
- sets the blocksize
- disables Transparent Huge Pages
- overrides the SELinux flag that disallows httpd to connect to the go process
- tunes some greenplum configuration
- enables remote and local access
- enables port 5432 on firewall
- makes greenplum a service

## Is Palette Greenplum Installer supported?

Palette Greenplum Installer is licensed under the GNU GPL v3 license. For professional support please contact developers@palette-software.com

Any bugs discovered should be filed in the [Palette Greenplum Installer Git issue tracker](https://github.com/palette-software/greenplum-installer/issues) or contribution is more than welcome.
