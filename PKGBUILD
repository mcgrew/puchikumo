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
backup=("etc/conf.d/uploadServer.conf")
options=()
install=
changelog=
source=(uploadServer.py uploadserver uploadServer.conf)
noextract=()
md5sums=('ff5393ad544bc030d0a777453746ad37'
         '4ed5429270dc5e31271a38beda639bd8'
         '96acc54e3617e32f8cc39d8f285c9c1e')

package() {
  cd "$srcdir"
  echo "#!/usr/bin/env python2" > $pkgdir/usr/bin/uploadserver
  tail -n +2 $srcdir/uploadServer.py >> $pkgdir/usr/bin/uploadserver
  chmod +x $pkgdir/usr/bin/uploadserver
  install -D uploadServer.conf ${pkgdir}/etc/conf.d/uploadServer.conf
  install -D uploadserver ${pkgdir}/etc/rc.d/uploadserver
}

# vim:set ts=2 sw=2 et:
