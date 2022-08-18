# Build an all-in-one puppetboard installer for apache WSGI
%{?!python3_pkgversion:%global python3_pkgversion 3.8}
%{?!puppetboard_version:%global puppetboard_version 4.0.3}
%global rpm_python_prefix python%{python3_version_nodots}
%global srcname puppetboard-monolith
%global puppetboard_basedir %{_datadir}/puppetboard
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
Source2:        content.tgz

BuildArch:      noarch

BuildRequires:  %{rpm_python_prefix}
BuildRequires:  %{rpm_python_prefix}-pip
BuildRequires:  %{rpm_python_prefix}-wheel
BuildRequires:  %{rpm_python_prefix}-setuptools
BuildRequires:  %{rpm_python_prefix}-rpm-macros

Requires(post): policycoreutils-python-utils
Requires(postun): policycoreutils-python-utils

Recommends: %{rpm_python_prefix}-mod_wsgi %{rpm_python_prefix}-%{srcname}

Provides: %{rpm_python_prefix}-%{srcname}
%{lua:
-- Declare a `Provides: bundle()` for each Python wheel
local rpm_python_prefix = rpm.expand('%{rpm_python_prefix}')
local src_file = rpm.expand('%{SOURCE1}')
local src_content = io.open(src_file, "r")
if src_content then
  for line in src_content:lines() do
      local rpmname = string.gsub( string.gsub(string.lower(line),'_','-'), '=', ') = ')
      print("Provides: bundle("..rpm_python_prefix.."-"..rpmname.."\n")
  end
end
}

%description %_description

%prep
rm -rf "%{name}-%{version}"
mkdir -p "%{name}-%{version}"
%setup -T -D -a 0  # unpack Source0 (python wheels)
%setup -T -D -a 2  # unpack Source2 (RPM content)


%install
install -m 0755 -d %{buildroot}%{puppetboard_basedir}/whl-puppetboard
install -m 0644 whl-puppetboard/* %{buildroot}%{puppetboard_basedir}/whl-puppetboard/

mkdir -p -m 0755 %{buildroot}%{puppetboard_basedir}/virtenv-puppetboard
mkdir -p -m 0755 %{buildroot}%{puppetboard_basedir}/puppetboard
mkdir -p -m 0755 %{buildroot}/%{_sysconfdir}/httpd/conf.d

install -m 0644 content/puppetboard/* %{buildroot}%{puppetboard_basedir}/puppetboard/
install -m 0644 content/httpd/puppetboard.conf %{buildroot}%{_sysconfdir}/httpd/conf.d/puppetboard.conf


%files  -n %{rpm_python_prefix}-%{srcname}
%attr(0755, puppetboard, puppetboard) %{puppetboard_basedir}/whl-puppetboard
%attr(0755, puppetboard, puppetboard) %{puppetboard_basedir}/virtenv-puppetboard
%attr(0755, puppetboard, puppetboard) %{puppetboard_basedir}/puppetboard
%config(noreplace) %{puppetboard_basedir}/puppetboard/settings.py
%config(noreplace) %{puppetboard_basedir}/puppetboard/wsgi.py
%config(noreplace) %{_sysconfdir}/httpd/conf.d/puppetboard.conf


%pre
getent group puppetboard >/dev/null || groupadd -g 854 -r puppetboard
getent passwd puppetboard >/dev/null || \
  useradd -r -u 854 -g puppetboard --create-home -s /sbin/nologin \
  -c "Account used by the %{name} package to own the puppetboard AIO & virtualenv" puppetboard
exit 0


%post
set -xeu -o pipefail # FIXME: remove before

if [ ! -f %{puppetboard_basedir}/virtenv-puppetboard/bin/activate ]; then
  runuser puppetboard -s /bin/bash -c "python%{python3_version} -m venv %{puppetboard_basedir}/virtenv-puppetboard"
fi
source %{puppetboard_basedir}/virtenv-puppetboard/bin/activate
runuser  puppetboard -s /bin/bash -c "pip%{python3_version} \
  install --no-index --find-links=file://%{puppetboard_basedir}/whl-puppetboard puppetboard==%{version}"

semanage fcontext --add --type httpd_sys_script_exec_t '%{puppetboard_basedir}/virtenv-puppetboard(/.*)?' 2>/dev/null || :
semanage fcontext --add --type httpd_sys_script_exec_t '%{puppetboard_basedir}/puppetboard(/.*)?' 2>/dev/null || :
restorecon -vv -R %{puppetboard_basedir} || :
systemctl condrestart httpd


%postun
if [ $1 -eq 0 ] ; then  # final removal
set -xeu -o pipefail
  rm -rf "%{puppetboard_basedir}/virtenv-puppetboard"
  userdel puppetboard
  semanage fcontext --delete --type httpd_sys_script_exec_t '%{puppetboard_basedir}/virtenv-puppetboard(/.*)?' 2>/dev/null || :
  semanage fcontext --delete --type httpd_sys_script_exec_t '%{puppetboard_basedir}/puppetboard(/.*)?' 2>/dev/null || :
  rmdir %{puppetboard_basedir} || : # remove only when empty
fi


#%%package -n  %%{rpm_python_prefix}-%%{srcname}-mod_wsgi-vhost
#Summary:    Optional Apache/WSGI VHOST
#Requires: %%{rpm_python_prefix}-mod_wsgi %%{rpm_python_prefix}-%%{srcname}
#
#%%description -n %%{rpm_python_prefix}-%%{srcname}-mod_wsgi-vhost
#Optional Apache/WSGI VHOST
#
#%%install -n %%{rpm_python_prefix}-%%{srcname}-mod_wsgi-vhost
#install -m 0755 -d %%{buildroot}%%{puppetboard_basedir}/puppetboard
#install -m 0755 -d
#install -m 0644 .../content/mod_wsgi-config/settings/* %%{
#install -m 0644 ../whl-puppetboard/* %%{buildroot}%%{puppetboard_basedir}/whl-puppetboard
#mkdir -p -m 0755 %%{buildroot}%%{puppetboard_basedir}/virtenv-puppetboard
#
#%%files -n  %%{rpm_python_prefix}-%%{srcname}-mod_wsgi-vhost


%changelog

* Fri Aug 05 2022 Chris Tessmer <chris.tessmer@onyxpoint.com> - 0.1.0
- Restructure RPM .spec file to build a re-usable SRPM
- Dynamically generate `Provides bundle()` for each Python .whl file
- Change basedir to %{_datadir}/puppetboard
- Recommend `python3x-mod_wsgi`

* Fri Jul 29 2022 Chris Tessmer <chris.tessmer@onyxpoint.com> - 0.1.0
- Create RPM
  - Add SELinux support
  - Add `puppetboard` user (using dynamic allocation)
