%define api 1
%define major 3
%define libname %mklibname dbus- %{api} %{major}
%define devname %mklibname -d dbus- %{api}
%global optflags %{optflags} -O3

Summary:	Linux D-Bus Message Broker
Name:		dbus-broker
Version:	23
Release:	3
License:	ASL 2.0
Group:		System/Servers
Url:		https://github.com/bus1/dbus-broker
Source0:	https://github.com/bus1/dbus-broker/releases/download/v%{version}/dbus-broker-%{version}.tar.xz
Patch0:		https://github.com/bus1/dbus-broker/commit/de03b7098bce71095673c21042a8f4b4f7c8c988.patch
Patch1:		https://github.com/bus1/dbus-broker/commit/03796aea364771811acc0e52c2bc0b55daa8a2e1.patch
Patch2:		dbus-broker-23-no-quota-for-root.patch
BuildRequires:	meson
BuildRequires:	systemd-macros
BuildRequires:	pkgconfig(libsystemd)
BuildRequires:	pkgconfig(audit)
BuildRequires:	pkgconfig(expat)
BuildRequires:	pkgconfig(dbus-1)
BuildRequires:	pkgconfig(libcap-ng)
BuildRequires:	pkgconfig(audit)
Requires:	dbus-common
Requires(pre):	shadow
%{?systemd_requires}
%rename dbus

%description
dbus-broker is an implementation of a message bus as defined by the D-Bus
specification. Its aim is to provide high performance and reliability, while
keeping compatibility to the D-Bus reference implementation. It is exclusively
written for Linux systems, and makes use of many modern features provided by
recent Linux kernel releases.

%prep
%autosetup -p1

%build
%serverbuild_hardened
%meson -Dselinux=false -Daudit=true -Ddocs=false -Dsystem-console-users=gdm,sddm,lightdm,lxdm -Dlinux-4-17=true

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
%systemd_post dbus-broker.service
%systemd_user_post dbus-broker.service
%journal_catalog_update

%preun
%systemd_preun dbus-broker.service
%systemd_user_preun dbus-broker.service

%postun
%systemd_postun dbus-broker.service
%systemd_user_postun dbus-broker.service

%triggerpostun -- dbus-daemon
if [ $2 -eq 0 ] ; then
# The `dbus-daemon` package used to provide the default D-Bus
# implementation. We continue to make sure that if you uninstall it, we
# re-evaluate whether to enable dbus-broker to replace it. If we didnt,
# you might end up without any bus implementation active.
    systemctl --no-reload          preset dbus-broker.service || :
    systemctl --no-reload --global preset dbus-broker.service || :
fi

%triggerin -- setup
if [ $1 -ge 2 ] || [ $2 -ge 2 ]; then

    if ! getent group messagebus >/dev/null 2>&1; then
	groupadd -r messagebus 2>/dev/null || :
    fi

    if ! getent passwd messagebus >/dev/null 2>&1; then
	useradd -r -g messagebus -d '/' -s /sbin/nologin -c "System message bus" messagebus 2>/dev/null ||:
    fi
fi

%files
%{_presetdir}/86-%{name}.preset
%{_bindir}/dbus-broker
%{_bindir}/dbus-broker-launch
%{_unitdir}/dbus-broker.service
%{_journalcatalogdir}/%{name}*.catalog
%{_userunitdir}/dbus-broker.service
