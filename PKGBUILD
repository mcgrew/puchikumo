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
md5sums=('5dcf892a22776fd6c5c517df21a35422'
         '56fa808ca3981e2752f9b53ea05e8a51'
         '96acc54e3617e32f8cc39d8f285c9c1e')

package() {
  cd "$srcdir"
  echo "#!/usr/bin/env python2" > $pkgdir/usr/bin/uploadserver
  tail -n +2 $srcdir/uploadServer.py >> $pkgdir/usr/bin/uploadserver
  install -D uploadServer.conf ${pkgdir}/etc/conf.d/uploadServer.conf
  install -D uploadserver ${pkgdir}/etc/rc.d/uploadserver
}

# vim:set ts=2 sw=2 et:
