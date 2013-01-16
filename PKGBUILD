# This is an example PKGBUILD file. Use this as a start to creating your own,
# and remove these comments. For more information, see 'man PKGBUILD'.
# NOTE: Please fill out the license field for your package! If it is unknown,
# then please put 'unknown'.

# Maintainer: Your Name <youremail@domain.com>
pkgname=uploadserver
pkgver=0.2.3
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
backup=("etc/conf.d/uploadServer.conf")
options=()
install=
changelog=
source=(uploadserver.py uploadserver uploadserver.conf)
noextract=()
md5sums=('3fa81986fee52b778ce95b6840a9b9e9'
         '400458cb52492858a787cf582fabe3a1'
         '36cea59a09eba4835f53c8947b86c866')
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
