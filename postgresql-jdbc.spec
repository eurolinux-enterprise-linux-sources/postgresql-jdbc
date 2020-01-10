# Note: although this is a noarch package, it will only build on x86 or x86_64
# hosts, because you need java-1.6.0-openjdk to build it and that is only
# provided in RHEL6 for those architectures.  (The resulting noarch package
# should work everywhere, though.)  To avoid having to retry builds in brew
# multiple times until you get the right build host, use
#	rhpkg build --target rhel-6.3-noarch-candidate
# (adjust branch number as appropriate).

# Caution: after building this package, it's a good idea to check the build
# log to make sure that the build script autoconfigured itself properly.
# You want to see at least "Configured build for the JDBC4 edition driver."


# Copyright (c) 2000-2005, JPackage Project
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the
#    distribution.
# 3. Neither the name of the JPackage Project nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

%global _gcj_support 0

%global gcj_support %{?_with_gcj_support:1}%{!?_with_gcj_support:%{?_without_gcj_support:0}%{!?_without_gcj_support:%{?_gcj_support:%{_gcj_support}}%{!?_gcj_support:0}}}

%global section		devel
%global upstreamver	8.4-704

Summary:	JDBC driver for PostgreSQL
Name:		postgresql-jdbc
Version:	8.4.704
Release:	2%{?dist}
# ASL 2.0 applies only to postgresql-jdbc.pom file, the rest is BSD
License:	BSD and ASL 2.0
Group:		Applications/Databases
URL:		http://jdbc.postgresql.org/

Source0:	http://jdbc.postgresql.org/download/%{name}-%{upstreamver}.src.tar.gz
# originally http://repo2.maven.org/maven2/postgresql/postgresql/8.4-701.jdbc4/postgresql-8.4-701.jdbc4.pom:
Source1:	postgresql-jdbc.pom
Patch1:		postgresql-jdbc-4.1.patch

%if ! %{gcj_support}
BuildArch:	noarch
%endif
BuildRequires:  java-devel >= 1:1.6.0
BuildRequires:  jpackage-utils
BuildRequires:  ant
BuildRequires:  ant-junit
BuildRequires:  junit
BuildRequires:	findutils
# gettext is only needed if we try to update translations
#BuildRequires:	gettext

%if %{gcj_support}
BuildRequires:	gcc-java
Requires(post): /usr/bin/rebuild-gcj-db
Requires(postun): /usr/bin/rebuild-gcj-db
%endif

# RHEL6 currently doesn't ship a modern JRE in all arches, so we must do this:
%ifarch %{ix86} x86_64
Requires: java >= 1:1.6.0
%else
Requires: java
%endif
Requires(post): jpackage-utils
Requires(postun): jpackage-utils

BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root

Obsoletes: rh-postgresql-jdbc

# We switched from arch to noarch build, so we need explicit Obsoletes:
# to ensure that the old arch-specific packages get removed during upgrade.
Obsoletes: postgresql-jdbc < 8.4.701-5
Obsoletes: postgresql-jdbc-debuginfo < 8.4.701-5

%description
PostgreSQL is an advanced Object-Relational database management
system. The postgresql-jdbc package includes the .jar files needed for
Java programs to access a PostgreSQL database.

%prep
%setup -c -q
mv -f %{name}-%{upstreamver}.src/* .
rm -f %{name}-%{upstreamver}.src/{.gitignore,.travis.yml}
rmdir %{name}-%{upstreamver}.src

# remove any binary libs
find -name "*.jar" -or -name "*.class" | xargs rm -f

%patch1 -p1

%build
export OPT_JAR_LIST="ant/ant-junit junit"
export CLASSPATH=

# Ideally we would run "sh update-translations.sh" here, but that results
# in inserting the build timestamp into the generated messages_*.class
# files, which makes rpmdiff complain about multilib conflicts if the
# different platforms don't build in the same minute.  For now, rely on
# upstream to have updated the translations files before packaging.

ant

%install
rm -rf ${RPM_BUILD_ROOT}

install -d $RPM_BUILD_ROOT%{_javadir}
# Per jpp conventions, jars have version-numbered names and we add
# versionless symlinks.
install -m 644 jars/postgresql.jar $RPM_BUILD_ROOT%{_javadir}/%{name}-%{version}.jar

pushd $RPM_BUILD_ROOT%{_javadir}
ln -s %{name}-%{version}.jar %{name}.jar
# Also, for backwards compatibility with our old postgresql-jdbc packages,
# add these symlinks.  (Probably only the jdbc3 symlink really makes sense?)
ln -s postgresql-jdbc.jar postgresql-jdbc2.jar
ln -s postgresql-jdbc.jar postgresql-jdbc2ee.jar
ln -s postgresql-jdbc.jar postgresql-jdbc3.jar
popd

%if %{gcj_support}
%{_bindir}/aot-compile-rpm
%endif

# Install the pom after inserting the correct version number
sed 's/UPSTREAM_VERSION/%{upstreamver}/g' %{SOURCE1} >JPP-postgresql-jdbc.pom
install -d -m 755 $RPM_BUILD_ROOT%{_mavenpomdir}/
install -m 644 JPP-postgresql-jdbc.pom $RPM_BUILD_ROOT%{_mavenpomdir}/JPP-postgresql-jdbc.pom
%add_to_maven_depmap postgresql postgresql %{version} JPP postgresql-jdbc

%clean
rm -rf $RPM_BUILD_ROOT

%post
%update_maven_depmap
%if %{gcj_support}
/usr/bin/rebuild-gcj-db
%endif

%postun
%update_maven_depmap
%if %{gcj_support}
/usr/bin/rebuild-gcj-db
%endif

%files
%defattr(-,root,root)
%doc LICENSE README doc/*
%{_javadir}/*
%if %{gcj_support}
%dir %{_libdir}/gcj/%{name}
%{_libdir}/gcj/%{name}/*.jar.so
%{_libdir}/gcj/%{name}/*.jar.db
%endif
%{_mavendepmapfragdir}/%{name}
%{_mavenpomdir}/JPP-%{name}.pom

%changelog
* Mon May 26 2014 Pavel Raiskup <praiskup@redhat.com> - 8.4.704-2
- revert back %%maven related changes from previous commit

* Mon May 26 2014 Pavel Raiskup <praiskup@redhat.com> - 8.4.704-1
- rebase to 8.4.704 (#816731)

* Sun May 20 2012 Tom Lane <tgl@redhat.com> 8.4.701-8
- Add explicit Obsoletes to get rid of old arch-specific packages,
  per discussions in bugs 821892 and 822206
Related: #816731

* Mon May  7 2012 Tom Lane <tgl@redhat.com> 8.4.701-7
- Tweak java Requires per Deepak Bhole's recommendation.
Related: #816731

* Mon May  7 2012 Tom Lane <tgl@redhat.com> 8.4.701-6
- Seems we can't Require java after all, per releng RT 152173.
Related: #816731

* Tue May  1 2012 Tom Lane <tgl@redhat.com> 8.4.701-5
- Switch to noarch (non-GCJ) build so that we can BuildRequire JDK >= 1.6;
  without this we don't get a JDBC4 driver at all, let alone 4.1.
Related: #816731

* Mon Apr 30 2012 Tom Lane <tgl@redhat.com> 8.4.701-4
- Add patch to provide some stub functions for JDBC 4.1 compatibility
Resolves: #816731
- Minor modernization of specfile, eg use maven directory macros,
  remove long-obsolete minimum versions from BuildRequires

* Thu Jan 14 2010 Tom Lane <tgl@redhat.com> 8.4.701-3
- Seems the .pom file *must* have a package version number in it, sigh
Resolves: #555582

* Mon Nov 23 2009 Tom Lane <tgl@redhat.com> 8.4.701-2
- Add a .pom file to ease use by maven-based packages (courtesy Deepak Bhole)
Resolves: #538487

* Tue Aug 18 2009 Tom Lane <tgl@redhat.com> 8.4.701-1
- Update to build 8.4-701

* Sun Jul 26 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0:8.3.603-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_12_Mass_Rebuild

* Tue Apr 21 2009 Tom Lane <tgl@redhat.com> 8.3.603-3
- Avoid multilib conflict caused by overeager attempt to rebuild translations

* Thu Feb 26 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0:8.3.603-2.1
- Rebuilt for https://fedoraproject.org/wiki/Fedora_11_Mass_Rebuild

* Wed Jul  9 2008 Tom "spot" Callaway <tcallawa@redhat.com> 8.3.603-1.1
- drop repotag

* Tue Feb 12 2008 Tom Lane <tgl@redhat.com> 8.3.603-1jpp
- Update to build 8.3-603

* Sun Aug 12 2007 Tom Lane <tgl@redhat.com> 8.2.506-1jpp
- Update to build 8.2-506

* Tue Apr 24 2007 Tom Lane <tgl@redhat.com> 8.2.505-1jpp
- Update to build 8.2-505
- Work around 1.4 vs 1.5 versioning inconsistency

* Fri Dec 15 2006 Tom Lane <tgl@redhat.com> 8.2.504-1jpp
- Update to build 8.2-504

* Wed Aug 16 2006 Tom Lane <tgl@redhat.com> 8.1.407-1jpp.4
- Fix Requires: for rebuild-gcj-db (bz #202544)

* Wed Aug 16 2006 Fernando Nasser <fnasser@redhat.com> 8.1.407-1jpp.3
- Merge with upstream

* Sat Jul 22 2006 Jakub Jelinek <jakub@redhat.com> 8.1.407-1jpp.2
- Rebuilt

* Wed Jul 12 2006 Jesse Keating <jkeating@redhat.com> - 0:8.1.407-1jpp.1
- rebuild

* Wed Jun 14 2006 Tom Lane <tgl@redhat.com> 8.1.407-1jpp
- Update to build 8.1-407

* Mon Mar 27 2006 Tom Lane <tgl@redhat.com> 8.1.405-2jpp
- Back-patch upstream fix to support unspecified-type strings.

* Thu Feb 16 2006 Tom Lane <tgl@redhat.com> 8.1.405-1jpp
- Split postgresql-jdbc into its own SRPM (at last).
- Build it from source.  Add support for gcj compilation.
