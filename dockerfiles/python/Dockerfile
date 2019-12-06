FROM centos/s2i-base-centos7

WORKDIR ${APP_ROOT}/src

ENV SUMMARY="Platform for building and running $PYTHON_VERSION applications" \
    DESCRIPTION="Python $PYTHON_VERSION container to run various python \
    applications. Inspired by https://github.com/sclorg/s2i-python-container/" \
    LANG=en_US.UTF-8 \
    GPG_KEY=0D96DF4D4110E5C43FBFB17F2D347EA6AA65421D \
    PYTHON_VERSION=3.7.5 \
    PYTHON_PIP_VERSION=19.3.1\
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
    "\
    && devDeps="\
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
    && yum install -y $devDeps \
    && yum install -y $INSTALL_PKGS \
    && export GNUPGHOME="$(mktemp -d)" \
    && gpg --keyserver ha.pool.sks-keyservers.net --recv-keys $GPG_KEY \
    && wget -q -O python.tar.xz "https://www.python.org/ftp/python/${PYTHON_VERSION%%[a-z]*}/Python-$PYTHON_VERSION.tar.xz" \
    && wget -q -O python.tar.xz.asc "https://www.python.org/ftp/python/${PYTHON_VERSION%%[a-z]*}/Python-$PYTHON_VERSION.tar.xz.asc" \
    && gpg --batch --verify python.tar.xz.asc python.tar.xz \
    && rm -r python.tar.xz.asc \
    && mkdir -p $SRC_DIR \
    && tar -xJC $SRC_DIR --strip-components=1 -f python.tar.xz \
    && rm python.tar.xz \
    && cd $SRC_DIR \
    && export EXTRATESTOPTS="-x test_gdb -x test_posix -x test_selectors -x test_mailbox" \
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
    && yum remove -y $devDeps \
    && yum clean all && rm -rf /var/cache/yum \
    && rm -rf ~/.cache $SRC_DIR


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
    && /usr/local/bin/python -m venv ${APP_ROOT} \
    && /opt/app-root/bin/pip install -U pip \
    && chown -R 1001:0 ${APP_ROOT} \
    && fix-permissions ${APP_ROOT} -P \
    && rpm-file-permissions

USER 1001

CMD $STI_SCRIPTS_PATH/usage
