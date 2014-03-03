# This is an example PKGBUILD file. Use this as a start to creating your own,
# and remove these comments. For more information, see 'man PKGBUILD'.
# NOTE: Please fill out the license field for your package! If it is unknown,
# then please put 'unknown'.

# Maintainer: Your Name <youremail@domain.com>
pkgname=uploadserver
pkgver=0.3_rc3
pkgrel=1
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
backup=("etc/conf.d/uploadserver.conf")
options=()
install=
changelog=
source=(uploadserver.py uploadserver uploadserver.conf)
noextract=()
md5sums=('2669b1669c7de4c1c152f96803cf507c'
         '377f9157f10b5f0394d156b11a3cf17c'
         '56b353bdc07ed5011f44799d2f3b8a7f')
package() {
  cd "$srcdir"
  mkdir -p "$pkgdir/usr/bin/"
  echo "#!/usr/bin/env python2" > $pkgdir/usr/bin/uploadserver
  tail -n +2 $srcdir/uploadserver.py >> $pkgdir/usr/bin/uploadserver
  chmod +x $pkgdir/usr/bin/uploadserver
  install -D uploadserver.conf ${pkgdir}/etc/conf.d/uploadserver.conf
  install -D uploadserver ${pkgdir}/etc/rc.d/uploadserver
}

# vim:set ts=2 sw=2 et:
