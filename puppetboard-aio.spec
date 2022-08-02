# python38 build
#   rpmdev-setuptree
#   dnf install -y python38-rpm-macros python38 python38-devel rpmdevtools
#   spectool --get-files --sourcedir pyt3.spec
# 
#
%{?!python3_pkgversion:%global python3_pkgversion 3.8}
%{?!puppetboard_version:%global puppetboard_version 4.0.3}
%global rpm_python_prefix python%{python3_version_nodots}
%global srcname puppetboard-aio
%global puppetboard_basedir /srv/puppetboard
%global _description %{expand:
Web frontend for Puppetboard
This package provides an all-in-one, no-internet virtualenv }

Name:           %{rpm_python_prefix}-%{srcname}
Version:        %{puppetboard_version}
Release:        0%{?dist}
Summary:        Web frontend for PuppetDB (Offline installer)
License:        Apache License 2.0
URL:            https://github.com/voxpupuli/puppetboard
Source0:        whl-puppetboard-python%{python3_version}.tgz
Source1:        requirements.txt

BuildArch:      noarch
BuildRequires:  %{rpm_python_prefix}
BuildRequires:  %{rpm_python_prefix}-pip
BuildRequires:  %{rpm_python_prefix}-wheel
BuildRequires:  %{rpm_python_prefix}-setuptools
BuildRequires:  %{rpm_python_prefix}-rpm-macros

Requires(post): policycoreutils-python-utils
Requires(postun): policycoreutils-python-utils

Provides: %{rpm_python_prefix}-%{srcname}
%{lua:
local rpm_python_prefix = rpm.expand('%{rpm_python_prefix}')
local src1 = rpm.expand('%{SOURCE1}')
local src1_content = io.open(src1, "r")
if src1_content then
  for line in src1_content:lines() do
      local rpmname = string.gsub( 
         string.gsub(string.lower(line),'_','-'),
        '=', ') = '
       )
      print("Provides: bundle("..rpm_python_prefix.."-"..rpmname.."\n")
  end
end
}

%description %_description

%prep
rm -rf "%{name}-%{version}"
mkdir -p "%{name}-%{version}"
%setup -D

%install
install -m 0755 -d %{buildroot}%{puppetboard_basedir}/whl-puppetboard
install -m 0644 ../whl-puppetboard/* %{buildroot}%{puppetboard_basedir}/whl-puppetboard
mkdir -p -m 0755 %{buildroot}%{puppetboard_basedir}/virtenv-puppetboard


%files  -n %{rpm_python_prefix}-%{srcname}
%attr(0755, puppetboard, puppetboard) %{puppetboard_basedir}/whl-puppetboard
%attr(0755, puppetboard, puppetboard) %{puppetboard_basedir}/virtenv-puppetboard



# TODO: set seltype
%pre
getent group puppetboard >/dev/null || groupadd -g 854 -r puppetboard
getent passwd puppetboard >/dev/null || \
  useradd -r -u 854 -g puppetboard -d /dev/null -s /sbin/nologin \
  -c "Account used by the %{name} package to own the puppetboard AIO & virtualenv" puppetboard
exit 0

%post
set -xeu -o pipefail

if [ ! -f %{puppetboard_basedir}/virtenv-puppetboard/bin/activate ]; then
  runuser puppetboard -s /bin/bash -c "python%{python3_version} -m venv %{puppetboard_basedir}/virtenv-puppetboard"
fi
source %{puppetboard_basedir}/virtenv-puppetboard/bin/activate
runuser  puppetboard -s /bin/bash -c "pip%{python3_version} \
  install --no-index --find-links=file://%{puppetboard_basedir}/whl-puppetboard puppetboard==%{version}"

semanage fcontext --add --type httpd_sys_script_exec_t '%{puppetboard_basedir}/virtenv-puppetboard(/.*)?' 2>/dev/null || :
restorecon -vv -R %{puppetboard_basedir}/virtenv-puppetboard || :


%postun
if [ $1 -eq 0 ] ; then  # final removal
set -xeu -o pipefail
  rm -rf "%{puppetboard_basedir}/virtenv-puppetboard"
  userdel puppetboard
  semanage fcontext --delete --type httpd_sys_script_exec_t '%{puppetboard_basedir}/virtenv-puppetboard(/.*)?' 2>/dev/null || :
  rmdir %{puppetboard_basedir} || : # remove, if empty
fi


#%package -n  %{rpm_python_prefix}-%{srcname}-mod_wsgi-vhost
#Summary:    Optional Apache/WSGI VHOST
#Requires: %{rpm_python_prefix}-mod_wsgi %{rpm_python_prefix}-%{srcname}
#%description  -n %{rpm_python_prefix}-%{srcname}-mod_wsgi-vhost 
#Optional Apache/WSGI VHOST
#%files -n  %{rpm_python_prefix}-%{srcname}-mod_wsgi-vhost
#%config(noreplace) %{_sysconfdir}/httpd/config.d/%{name}.conf


%changelog
