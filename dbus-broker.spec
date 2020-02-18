%define _userunitdir /lib/systemd/
%define api 1
%define major 3
%define libname %mklibname dbus- %{api} %{major}
%define devname %mklibname -d dbus- %{api}

Summary:	Linux D-Bus Message Broker
Name:		dbus-broker
Version:	22
Release:	1
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
%meson -Dselinux=false -Daudit=false -Ddocs=false

%meson_build

%install
%meson_install

%files
%{_bindir}/dbus-broker
%{_bindir}/dbus-broker-launch
%{_usernitdir}/catalog/dbus-broker-launch.catalog
%{_userunitdir}/catalog/dbus-broker.catalog
%{_userunitdir}/user/dbus-broker.service
/lib/systemd/system/dbus-broker.service
