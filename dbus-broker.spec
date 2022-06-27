%define api 1
%define major 3
%define libname %mklibname dbus- %{api} %{major}
%define devname %mklibname -d dbus- %{api}
%global optflags %{optflags} -O3

Summary:	Linux D-Bus Message Broker
Name:		dbus-broker
Version:	31
Release:	5
License:	ASL 2.0
Group:		System/Servers
Url:		https://github.com/bus1/dbus-broker
Source0:	https://github.com/bus1/dbus-broker/releases/download/v%{version}/dbus-broker-%{version}.tar.xz
Source1:	dbus-broker.sysusers
Patch0:		dbus-broker-23-no-quota-for-root.patch
Patch1:		https://raw.githubusercontent.com/clearlinux-pkgs/dbus-broker/master/use-private-network.patch
BuildRequires:	meson
BuildRequires:	systemd-rpm-macros
BuildRequires:	pkgconfig(libsystemd)
BuildRequires:	pkgconfig(expat)
BuildRequires:	pkgconfig(dbus-1)
BuildRequires:	pkgconfig(libcap-ng)
Requires:	dbus-common
Requires(pre):	shadow
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
%meson -Dselinux=false -Daudit=false -Ddocs=false -Dsystem-console-users=gdm,sddm,lightdm,lxdm -Dlinux-4-17=true

%meson_build

%install
%meson_install

install -d %{buildroot}%{_presetdir}
cat > %{buildroot}%{_presetdir}/86-%{name}.preset << EOF
enable %{name}.service
EOF

mkdir -p %{buildroot}%{_sysusersdir}
install -c -m 644 %{S:1} %{buildroot}%{_sysusersdir}/%{name}.conf

%check
%meson_test

%pre
%sysusers_create_package %{name} %{S:1}

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
if [ $2 -eq 0 ] && [ -x /usr/bin/systemctl ] ; then
# The `dbus-daemon` package used to provide the default D-Bus
# implementation. We continue to make sure that if you uninstall it, we
# re-evaluate whether to enable dbus-broker to replace it. If we didnt,
# you might end up without any bus implementation active.
    systemctl --no-reload          preset dbus-broker.service || :
    systemctl --no-reload --global preset dbus-broker.service || :
fi

%files
%{_presetdir}/86-%{name}.preset
%{_bindir}/dbus-broker
%{_bindir}/dbus-broker-launch
%{_unitdir}/dbus-broker.service
%{_journalcatalogdir}/%{name}*.catalog
%{_userunitdir}/dbus-broker.service
%{_sysusersdir}/%{name}.conf
