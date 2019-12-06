FROM centos/s2i-base-centos7

WORKDIR ${APP_ROOT}/src

ENV SUMMARY="Platform for building and running $PYTHON_VERSION applications" \
    DESCRIPTION="Python $PYTHON_VERSION container to run various python \
    applications. Inspired by https://github.com/sclorg/s2i-python-container/" \
    LANG=en_US.UTF-8 \
    GPG_KEY='0D96DF4D4110E5C43FBFB17F2D347EA6AA65421D F2A38D7EEB2B66405761070D0ADEE10094604D37 0x249B39D24F25E3B6 0x2071B08A33BD3F06 0x04376F3EE0856959 0xBCEF7E294B092E28' \
    PYTHON_VERSION=3.7.5 \
    PYTHON_PIP_VERSION=19.3.1\
    LIBGPG_ERROR_VERSION=1.36 \
    LIBGCRYPT_VERSION=1.8.5 \
    GNUPG_VERSION=2.2.18 \
    LIBKSBA_VERSION=1.3.5 \
    LIBASSUAN_VERSION=2.5.3 \
    NTBTLS_VERSION=0.1.2 \
    NPTH_VERSION=1.6 \
    GPGME_VERSION=1.13.1 \
    GPG_SRC_DIR=/usr/src/gpg \
    SRC_DIR=/usr/src/python3 \
    PATH=/opt/app-root/src/bin:/opt/app-root/bin:/usr/local/bin:$PATH\
    GNUPGHOME=/tmp/gnupg


LABEL summary="$SUMMARY" \
      description="$DESCRIPTION" \
      io.k8s.description="$DESCRIPTION" \
      io.k8s.display-name="Python $PYTHON_VERSION" \
      io.openshift.tags="builder,python,python37" \
      version="1" \
    maintainer="atlorenzo@email.arizona.edu"

COPY ./contrib/ /opt/app-root
COPY ./s2i/bin/ $STI_SCRIPTS_PATH

RUN set -ex \
    && INSTALL_PKGS="\
      expat \
      expat-devel \
      nss_wrapper \
      xz-devel \
      libffi-devel \
      devtoolset-8-gcc \
      devtoolset-8-gcc-c++ \
      " \
    && buildDeps=' \
      bzip2-devel \
      readline-devel \
      xz-compat-libs \
    ' \
    && yum update -y \
    && yum install -y centos-release-scl \
    && yum install -y $buildDeps \
    && yum install -y $INSTALL_PKGS \
    && mkdir -p $GNUPGHOME \
    && chmod -R 700 $GNUPGHOME \
    && gpg --keyserver ha.pool.sks-keyservers.net --recv-keys $GPG_KEY \
    && wget -q -O python.tar.xz "https://www.python.org/ftp/python/${PYTHON_VERSION%%[a-z]*}/Python-$PYTHON_VERSION.tar.xz" \
    && wget -q -O python.tar.xz.asc "https://www.python.org/ftp/python/${PYTHON_VERSION%%[a-z]*}/Python-$PYTHON_VERSION.tar.xz.asc" \
    && gpg --batch --verify python.tar.xz.asc python.tar.xz \
    && rm -r python.tar.xz.asc \
    && mkdir -p $SRC_DIR \
    && tar -xJC $SRC_DIR --strip-components=1 -f python.tar.xz \
    && rm python.tar.xz \
    && cd $SRC_DIR \
    && export EXTRATESTOPTS="-x test_gdb -x test_posix -x test_selectors" \
    && source scl_source enable devtoolset-8 \
    && ./configure \
    --enable-shared \
    --build=x86_64-redhat-linux-gnu \
    --host=x86_64-redhat-linux-gnu \
    --enable-ipv6 \
    --with-computed-gotos=yes \
    --with-system-expat \
    --with-ensurepip=yes \
    --enable-loadable-sqlite-extensions \
    && make -j$(nproc) \
    && make test \
    && make install \
    && echo '/usr/local/lib' > /etc/ld.so.conf.d/local.conf \
    && ldconfig \
    && if [ ! -e /usr/local/bin/pip3 ]; then : \
       && wget -O /tmp/get-pip.py 'https://bootstrap.pypa.io/get-pip.py' \
       && python3 /tmp/get-pip.py "pip==$PYTHON_PIP_VERSION" \
       && rm /tmp/get-pip.py \
    ; fi \
    # we use "--force-reinstall" for the case where the version of pip
    # we're trying to install is the same as the version bundled with Python
    # ("Requirement already up-to-date: pip==8.1.2 in
    # /usr/local/lib/python3.6/site-packages")
    # https://github.com/docker-library/python/pull/143#issuecomment-241032683
    && pip3 install --no-cache-dir --upgrade --force-reinstall "pip==$PYTHON_PIP_VERSION" \
    # then we use "pip list" to ensure we don't have more than one pip
    # version installed
    # https://github.com/docker-library/python/pull/100
    && [ "$(pip list |tac|tac| awk -F '[ ()]+' '$1 == "pip" { print $2; exit }')" = "$PYTHON_PIP_VERSION" ] \
    \
    && find /usr/local -depth \
    \( \
         \( -type d -a -name test -o -name tests \) \
         -o \
         \( -type f -a -name '*.pyc' -o -name '*.pyo' \) \
    \) -exec rm -rf '{}' + \
    && yum autoremove -y $buildDeps \
    && yum clean all && rm -rf /var/cache/yum \
    && rm -rf ~/.cache $SRC_DIR

RUN set -ex \
    && wget -q -O automake.tar.gz "http://ftp.gnu.org/gnu/automake/automake-1.16.1.tar.gz" \
    && wget -q -O automake.tar.gz.sig "http://ftp.gnu.org/gnu/automake/automake-1.16.1.tar.gz.sig" \
    && gpg --batch --verify automake.tar.gz.sig automake.tar.gz \
    && rm -r automake.tar.gz.sig \
    && mkdir -p $GPG_SRC_DIR/automake \
    && tar -xzC $GPG_SRC_DIR/automake --strip-components=1 -f automake.tar.gz \
    && rm automake.tar.gz \
    && cd $GPG_SRC_DIR/automake \
    && ./configure --prefix /usr/local \
    && make install \
    && ldconfig \
    && libs=( libgpg-error libgcrypt libksba libassuan ntbtls npth gnupg ) \
    && versions=( $LIBGPG_ERROR_VERSION $LIBGCRYPT_VERSION $LIBKSBA_VERSION $LIBASSUAN_VERSION $NTBTLS_VERSION $NPTH_VERSION $GNUPG_VERSION ) \
    && for i in "${!libs[@]}"; do \
        cd $APP_ROOT/src \
        && wget -q -O ${libs[i]}.tar.bz2 "https://gnupg.org/ftp/gcrypt/${libs[i]}/${libs[i]}-${versions[i]}.tar.bz2" \
        && wget -q -O ${libs[i]}.tar.bz2.sig "https://gnupg.org/ftp/gcrypt/${libs[i]}/${libs[i]}-${versions[i]}.tar.bz2.sig" \
        && gpg --batch --verify ${libs[i]}.tar.bz2.sig ${libs[i]}.tar.bz2 \
        && rm -r ${libs[i]}.tar.bz2.sig \
        && mkdir -p $GPG_SRC_DIR/${libs[i]} \
        && tar -xjC $GPG_SRC_DIR/${libs[i]} --strip-components=1 -f ${libs[i]}.tar.bz2 \
        && rm ${libs[i]}.tar.bz2 \
        && cd $GPG_SRC_DIR/${libs[i]} \
        && sh ./autogen.sh \
        && ./configure --prefix /usr/local \
        && make -j$(nproc) install \
        && ldconfig \
    ; done \
    && buildDeps=' \
    swig \
    texinfo \
    ' \
    && yum install -y $buildDeps \
    && source scl_source enable devtoolset-8 \
    && cd $APP_ROOT/src \
    && wget -q -O gpgme.tar.bz2 "https://gnupg.org/ftp/gcrypt/gpgme/gpgme-$GPGME_VERSION.tar.bz2" \
    && wget -q -O gpgme.tar.bz2.sig "https://gnupg.org/ftp/gcrypt/gpgme/gpgme-$GPGME_VERSION.tar.bz2.sig" \
    && gpg --batch --verify gpgme.tar.bz2.sig gpgme.tar.bz2 \
    && rm -r gpgme.tar.bz2.sig \
    && mkdir -p $GPG_SRC_DIR/gpgme \
    && tar -xjC $GPG_SRC_DIR/gpgme --strip-components=1 -f gpgme.tar.bz2 \
    && rm gpgme.tar.bz2 \
    && cd $GPG_SRC_DIR/gpgme \
    && sh ./autogen.sh \
    && ./configure --prefix /usr/local CFLAGS="-std=c11" \
    && make -j$(nproc) install \
    && ldconfig \
    && yum autoremove -y $buildDeps \
    && yum clean all && rm -rf /var/cache/yum \
    && rm -rf ~/.cache $GPG_SRC_DIR

# make some useful symlinks that are expected to exist
RUN set -ex \
    && cd /usr/local/bin \
    && { [ -e easy_install ] || ln -s easy_install-* easy_install; } \
    && ln -s idle3 idle \
    && ln -s pydoc3 pydoc \
    && ln -s python3 python \
    && ln -s python3-config python-config \
    # Create a Python virtual environment for use by any application to avoid
    # potential conflicts with Python packages preinstalled in the main Python
    # installation. Use system python-gpg
    && /usr/local/bin/python -m venv --system-site-packages ${APP_ROOT} \
    && /opt/app-root/bin/pip install -U pip \
    && chown -R 1001:0 ${APP_ROOT} \
    && fix-permissions ${APP_ROOT} -P \
    && rpm-file-permissions

USER 1001

CMD $STI_SCRIPTS_PATH/usage
