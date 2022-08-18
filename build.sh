#!/bin/bash
set -e -u -o pipefail
SPEC_FILE=puppetboard-aio.spec
PUPPETBOARD_VERSION="${PUPPETBOARD_VERSION:-4.0.3}"
TARGET_PYTHON3="${TARGET_PYTHON3:-3.8}"
PIP_EXE="pip${TARGET_PYTHON3}"

OLD_HOME="$HOME"

# rpmdevtools are hard-coded to use $HOME for user builds :facepalm"
HOME="${RPMBUILD_PARENT_DIR:-$PWD}"

rm -rf whl-puppetboard rpmbuild
rpmdev-setuptree
rpmdev-wipetree
srcdir="$(rpm --eval=%_sourcedir)"
topdir="$(rpm --eval=%_topdir)"

# SOURCE0: puppetboard and all python requirements, as .whl files
"$PIP_EXE" download \
  --destination-directory "_whl/python-${TARGET_PYTHON3}/whl-puppetboard" \
  puppetboard=="${PUPPETBOARD_VERSION}"
tar -C"_whl/python-${TARGET_PYTHON3}" -zcvf "$srcdir/whl-puppetboard-python${TARGET_PYTHON3}.tgz" whl-puppetboard

# SOURCE1: requirements.txt file, generated from the .whl files in SOURCE0
#  There are better ways to do this
cd "_whl/python-${TARGET_PYTHON3}/whl-puppetboard/"
ls -1 *.whl | sed -e 's/^\([A-Za-z0-9_]\+\)-/\1=/' -e 's/-.*$//'  > "$srcdir/requirements.txt"
cd -

# SOURCE2: this repo's additional content (WSGI script, config files, etc)
tar zcvf "$srcdir/content.tgz" content


rpmspec --parse "$SPEC_FILE" \
  --define="lua_debug 0" \
  --define="puppetboard_version $PUPPETBOARD_VERSION" \
  --define="python3_pkgversion ${TARGET_PYTHON3}" \
  --define="__python3 python${TARGET_PYTHON3}" \
  --define="__python python${TARGET_PYTHON3}" \
 > _parsed-by-rpmpec.spec

spectool --get-files --sourcedir "$SPEC_FILE" \
  --define="puppetboard_version $PUPPETBOARD_VERSION" \
  --define="python3_pkgversion ${TARGET_PYTHON3}" \
  --define="__python3 python${TARGET_PYTHON3}" \
  --define="__python python${TARGET_PYTHON3}"

rpmbuild \
  -ba \
  --define="lua_debug 0" \
  --define="puppetboard_version $PUPPETBOARD_VERSION" \
  --define="python3_pkgversion ${TARGET_PYTHON3}" \
  --define="__python3 python${TARGET_PYTHON3}" \
  --define="__python python${TARGET_PYTHON3}" \
  "$SPEC_FILE"  |& tee _build.log

cd "$HOME"
HOME="$OLD_HOME"

printf "\n\n===============================================================================\n\n"

sudo dnf install ./rpmbuild/RPMS/noarch/python38-puppetboard-monolith-${PUPPETBOARD_VERSION}-?.el8.noarch.rpm -y
