FROM python:latest

WORKDIR ${APP_ROOT}/src

ENV SUMMARY="Add the extra system packages to python base incl. GPG, wgrib2, pandoc" \
    LANG=en_US.UTF-8 \
    GPG_KEY='F2A38D7EEB2B66405761070D0ADEE10094604D37 0x249B39D24F25E3B6 0x2071B08A33BD3F06 0x04376F3EE0856959 0xBCEF7E294B092E28' \
    LIBGPG_ERROR_VERSION=1.36 \
    LIBGCRYPT_VERSION=1.8.5 \
    GNUPG_VERSION=2.2.18 \
    LIBKSBA_VERSION=1.3.5 \
    LIBASSUAN_VERSION=2.5.3 \
    NTBTLS_VERSION=0.1.2 \
    NPTH_VERSION=1.6 \
    GPGME_VERSION=1.13.1 \
    GPG_SRC_DIR=/usr/src/gpg

LABEL summary="$SUMMARY" \
      maintainer="atlorenzo@email.arizona.edu"

USER root

RUN set -ex \
    && buildDeps=' \
    swig \
    texinfo \
    ' \
    && gccDeps='\
    devtoolset-8-gcc \
    devtoolset-8-gcc-c++ \
    ' \
    && yum update - y \
    && yum install -y $buildDeps \
    && yum install -y $gccDeps \
    && wget -q -O automake.tar.gz "http://ftp.gnu.org/gnu/automake/automake-1.16.1.tar.gz" \
    && wget -q -O automake.tar.gz.sig "http://ftp.gnu.org/gnu/automake/automake-1.16.1.tar.gz.sig" \
    && wget -q -O gpgme.tar.bz2 "https://gnupg.org/ftp/gcrypt/gpgme/gpgme-$GPGME_VERSION.tar.bz2" \
    && wget -q -O gpgme.tar.bz2.sig "https://gnupg.org/ftp/gcrypt/gpgme/gpgme-$GPGME_VERSION.tar.bz2.sig" \
    && export GNUPGHOME="$(mktemp -d)" \
    && gpg --keyserver ha.pool.sks-keyservers.net --recv-keys $GPG_KEY \
    && gpg --batch --verify automake.tar.gz.sig automake.tar.gz \
    && rm -r automake.tar.gz.sig \
    && mkdir -p $GPG_SRC_DIR/automake \
    && tar -xzC $GPG_SRC_DIR/automake --strip-components=1 -f automake.tar.gz \
    && rm automake.tar.gz \
    && gpg --batch --verify gpgme.tar.bz2.sig gpgme.tar.bz2 \
    && rm -r gpgme.tar.bz2.sig \
    && mkdir -p $GPG_SRC_DIR/gpgme \
    && tar -xjC $GPG_SRC_DIR/gpgme --strip-components=1 -f gpgme.tar.bz2 \
    && rm gpgme.tar.bz2 \
    && libs=( libgpg-error libgcrypt libksba libassuan ntbtls npth gnupg ) \
    && versions=( $LIBGPG_ERROR_VERSION $LIBGCRYPT_VERSION $LIBKSBA_VERSION $LIBASSUAN_VERSION $NTBTLS_VERSION $NPTH_VERSION $GNUPG_VERSION ) \
    && for i in "${!libs[@]}"; do \
        wget -q -O ${libs[i]}.tar.bz2 "https://gnupg.org/ftp/gcrypt/${libs[i]}/${libs[i]}-${versions[i]}.tar.bz2" \
        && wget -q -O ${libs[i]}.tar.bz2.sig "https://gnupg.org/ftp/gcrypt/${libs[i]}/${libs[i]}-${versions[i]}.tar.bz2.sig" \
        && gpg --batch --verify ${libs[i]}.tar.bz2.sig ${libs[i]}.tar.bz2 \
        && rm -r ${libs[i]}.tar.bz2.sig \
        && mkdir -p $GPG_SRC_DIR/${libs[i]} \
        && tar -xjC $GPG_SRC_DIR/${libs[i]} --strip-components=1 -f ${libs[i]}.tar.bz2 \
        && rm ${libs[i]}.tar.bz2 \
    ; done \
    && cd $GPG_SRC_DIR/automake \
    && ./configure --prefix /usr/local \
    && make install \
    && ldconfig \
    && for i in "${!libs[@]}"; do \
        cd $GPG_SRC_DIR/${libs[i]} \
        && sh ./autogen.sh \
        && ./configure --prefix /usr/local \
        && make -j$(nproc) install \
        && ldconfig \
    ; done \
    && cd $GPG_SRC_DIR/gpgme \
    && source scl_source enable devtoolset-8 \
    && sh ./autogen.sh \
    && ./configure --prefix /usr/local CFLAGS="-std=c11" \
    && make -j$(nproc) install \
    && ldconfig \
    && yum autoremove -y $buildDeps \
    && yum remove -y $gccDeps \
    && yum clean all && rm -rf /var/cache/yum \
    && rm -rf ~/.cache $GPG_SRC_DIR $GNUPGHOME

# link gpgme python package to virtual env
# install wgrib2
# install phantomjs
# chown things
RUN set -ex \
    && export PYTHON_MAJOR_VER="$(python -V | awk '{print $2}' | cut -d. -f-2)" \
    && ln -s "/usr/local/lib/python$PYTHON_MAJOR_VER/site-packages/gpg" "/opt/app-root/lib/python$PYTHON_MAJOR_VER/site-packages/" \
    && /opt/app-root/bin/python -c "import gpg" \
    && yum install -y epel-release  \
    && yum install -y --setopt=tsflags=nodocs wgrib2 \
    && yum clean all \
    && rm -rf /var/cache/yum \
    && wget -q -O phantomjs.tar.bz2 https://bitbucket.org/ariya/phantomjs/downloads/phantomjs-2.1.1-linux-x86_64.tar.bz2 \
    && mkdir phantomjs \
    && tar -xjC ./phantomjs --strip-components=1 -f phantomjs.tar.bz2 \
    && cp phantomjs/bin/phantomjs /opt/app-root/bin/. \
    && rm -r phantomjs phantomjs.tar.bz2 \
    && chown -R 1001:0 ${APP_ROOT} \
    && fix-permissions ${APP_ROOT} -P \
    && mkdir /data \
    && chown root:5555 /data \
    && chmod 0775 /data

USER 1001
