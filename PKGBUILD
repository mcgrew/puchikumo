# This is an example PKGBUILD file. Use this as a start to creating your own,
# and remove these comments. For more information, see 'man PKGBUILD'.
# NOTE: Please fill out the license field for your package! If it is unknown,
# then please put 'unknown'.

# Maintainer: Your Name <youremail@domain.com>
pkgname=pipeline-upload-server
pkgver=0.2
pkgrel=2
epoch=
pkgdesc=""
arch=(any)
url=""
license=('GPL')
groups=()
depends=()
makedepends=()
checkdepends=()
optdepends=()
provides=()
conflicts=()
replaces=()
backup=()
options=()
install=
changelog=
source=(uploadServer.py uploadserver uploadServer.conf)
noextract=()
md5sums=('85ab04f608d12f9d3e528d44200fd765'
         '3b371fd885c77e7219433fc5e873bf95'
         '8d1526844eb7d7ae85771d95019ffc5a')

package() {
  cd "$srcdir"
  echo "#!/usr/bin/env python2" > $pkgdir/usr/bin/uploadserver
  tail -n +2 $srcdir/uploadServer.py >> $pkgdir/usr/bin/uploadserver
  install -D uploadServer.conf ${pkgdir}/etc/conf.d/uploadServer.conf
  install -D uploadserver ${pkgdir}/etc/rc.d/uploadserver
}

# vim:set ts=2 sw=2 et:
