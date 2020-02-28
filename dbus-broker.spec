%define api 1
%define major 3
%define libname %mklibname dbus- %{api} %{major}
%define devname %mklibname -d dbus- %{api}
%global optflags %{optflags} -O3

Summary:	Linux D-Bus Message Broker
Name:		dbus-broker
Version:	22
Release:	"BIG FAT WARNING !!! Consult TPG before you build this package. It needs lot of changes inside dbus package prior to release this one"
License:	ASL 2.0
Group:		System/Servers
Url:		https://github.com/bus1/dbus-broker
Source0:	https://github.com/bus1/dbus-broker/releases/download/v%{version}/dbus-broker-%{version}.tar.xz
BuildRequires:	meson
BuildRequires:	systemd-macros
BuildRequires:	pkgconfig(libsystemd)
BuildRequires:	pkgconfig(audit)
BuildRequires:	pkgconfig(expat)
BuildRequires:	pkgconfig(dbus-1)
BuildRequires:	pkgconfig(libcap-ng)
%{?systemd_requires}
%rename dbus

%description
dbus-broker is an implementation of a message bus as defined by the D-Bus
specification. Its aim is to provide high performance and reliability, while
keeping compatibility to the D-Bus reference implementation. It is exclusively
written for Linux systems, and makes use of many modern features provided by
recent Linux kernel releases.


%prep
%setup -q

%build
%serverbuild_hardened
%meson -Dselinux=false -Daudit=false -Ddocs=false -Dsystem-console-users=gdm -Dlinux-4-17=true

%meson_build

%install
%meson_install

install -d %{buildroot}%{_presetdir}
cat > %{buildroot}%{_presetdir}/86-%{name}.preset << EOF
enable %{name}.service
EOF

%check
%meson_test

%pre
# create dbus user and group
getent group messagebus >/dev/null || groupadd -f -g messagebus -r messagebus
if ! getent passwd messagebus >/dev/null ; then
    if ! getent passwd messagebus >/dev/null ; then
	useradd -r -u messagebus -g messagebus -d '/' -s /sbin/nologin -c "System message bus" messagebus
    else
	useradd -r -g messagebus -d '/' -s /sbin/nologin -c "System message bus" messagebus
    fi
fi
exit 0

%post
# systemd has special checks if dbus.socket and dbus.service are active and
# will close the dbus connection if they are not. When the symlinks are changed
# from dbus-daemon to dbus-broker, systemd would think that dbus is gone,
# because dbus.service (which now is an alias for dbus-broker.service) is not
# active. Let's add a temporary override that will keep pid1 happy.
if [ $1 -eq 1 ] ; then
    if systemctl is-enabled -q dbus-daemon.service; then
# Install a temporary generator that'll keep providing the
# alias as it was.
	mkdir -p /run/systemd/system-generators/
	cat >>/run/systemd/system-generators/dbus-symlink-generator <<EOF
#!/bin/sh
ln -s %{_unitdir}/dbus-daemon.service \$2/dbus.service
EOF
	chmod +x /run/systemd/system-generators/dbus-symlink-generator
	chcon system_u:object_r:init_exec_t:s0 /run/systemd/system-generators/dbus-symlink-generator || :
    fi
    if systemctl is-enabled -q --global dbus-daemon.service; then
	mkdir -p /run/systemd/user-generators/
	cat >>/run/systemd/user-generators/dbus-symlink-generator <<EOF
#!/bin/sh
ln -s %{_userunitdir}/dbus-daemon.service \$2/dbus.service
EOF
	chmod +x /run/systemd/user-generators/dbus-symlink-generator
    fi

    systemctl --no-reload -q disable dbus-daemon.service || :
    systemctl --no-reload -q --global disable dbus-daemon.service || :
    systemctl --no-reload -q enable dbus-broker.service || :
    systemctl --no-reload -q --global enable dbus-broker.service || :
fi

%triggerpostun -- dbus-daemon
if [ $2 -eq 0 ]; then
    systemctl --no-reload enable dbus-broker.service || :
    systemctl --no-reload --global enable dbus-broker.service || :
fi

%files
%{_presetdir}/86-%{name}.preset
%{_bindir}/dbus-broker
%{_bindir}/dbus-broker-launch
%{_unitdir}/dbus-broker.service
%{_journalcatalogdir}/%{name}*.catalog
%{_userunitdir}/dbus-broker.service
