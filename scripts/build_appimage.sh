#!/bin/bash
set -e

# Directories
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="${PROJECT_ROOT}/build"
DIST_DIR="${PROJECT_ROOT}/dist"
APPDIR="${BUILD_DIR}/AppDir"

echo "=== 1. Cleaning up previous builds ==="
rm -rf "${BUILD_DIR}"
rm -rf "${DIST_DIR}"
mkdir -p "${BUILD_DIR}"
mkdir -p "${DIST_DIR}"

echo "=== 2. Building standalone package with PyInstaller ==="
cd "${PROJECT_ROOT}"
uv run --with pyinstaller pyinstaller --noconfirm --clean --onedir \
  --add-data "src/ballbreaker/resources:resources" \
  --name ballbreaker \
  src/ballbreaker/__main__.py

echo "=== 3. Creating AppDir structure ==="
mkdir -p "${APPDIR}/usr/bin"
mkdir -p "${APPDIR}/usr/lib"
mkdir -p "${APPDIR}/usr/share/applications"
mkdir -p "${APPDIR}/usr/share/icons/hicolor/256x256/apps"

# Copy PyInstaller distribution to AppDir/usr/lib/ballbreaker
cp -r "${DIST_DIR}/ballbreaker" "${APPDIR}/usr/lib/ballbreaker"

# Create a wrapper in usr/bin/ballbreaker
cat << 'EOF' > "${APPDIR}/usr/bin/ballbreaker"
#!/bin/sh
SELF=$(readlink -f "$0")
HERE=$(dirname "$SELF")
exec "${HERE}/../lib/ballbreaker/ballbreaker" "$@"
EOF
chmod +x "${APPDIR}/usr/bin/ballbreaker"

echo "=== 4. Creating desktop file and icons ==="
# Desktop Entry
cat << 'EOF' > "${APPDIR}/usr/share/applications/ballbreaker.desktop"
[Desktop Entry]
Type=Application
Name=Ballbreaker
Exec=ballbreaker %F
Icon=ballbreaker
Comment=Modern Linux GUI and CLI application for installing desktop entries for tarballs
Terminal=false
Categories=Utility;Development;
EOF

# Copy Icon
cp "${PROJECT_ROOT}/src/ballbreaker/resources/icon.png" "${APPDIR}/usr/share/icons/hicolor/256x256/apps/ballbreaker.png"

# AppDir Root requirements: AppRun, ballbreaker.desktop, ballbreaker.png
# AppRun entrypoint
cat << 'EOF' > "${APPDIR}/AppRun"
#!/bin/sh
SELF=$(readlink -f "$0")
HERE=$(dirname "$SELF")
export PATH="${HERE}/usr/bin:${PATH}"
export LD_LIBRARY_PATH="${HERE}/usr/lib/ballbreaker:${LD_LIBRARY_PATH}"
exec "${HERE}/usr/lib/ballbreaker/ballbreaker" "$@"
EOF
chmod +x "${APPDIR}/AppRun"

# Root links
ln -s usr/share/applications/ballbreaker.desktop "${APPDIR}/ballbreaker.desktop"
ln -s usr/share/icons/hicolor/256x256/apps/ballbreaker.png "${APPDIR}/ballbreaker.png"

echo "=== 5. Downloading and running appimagetool ==="
# Download appimagetool continuous release if not already downloaded
APPIMAGETOOL="${BUILD_DIR}/appimagetool"
if [ ! -f "${APPIMAGETOOL}" ]; then
  echo "Downloading appimagetool..."
  curl -L -o "${APPIMAGETOOL}" "https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage"
  chmod +x "${APPIMAGETOOL}"
fi

# Run appimagetool (using extract-and-run for sandbox safety)
echo "Packaging AppDir into AppImage..."
export ARCH=x86_64
"${APPIMAGETOOL}" --appimage-extract-and-run "${APPDIR}" "${DIST_DIR}/Ballbreaker-x86_64.AppImage"

echo "=== Build Complete! ==="
echo "AppImage is located at: ${DIST_DIR}/Ballbreaker-x86_64.AppImage"
