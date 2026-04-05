#!/bin/bash
# Download all data and models needed for this environment.
#
# IMPORTANT: Use TMPDIR=/dev/shm because /tmp is a 64MB tmpfs that fills up.
set -e
export TMPDIR=/dev/shm
cd "$(dirname "$0")"
cd ..

echo "=== Downloading datasets ==="

# Common Shapes dataset
COMMON_SHAPES_DIR="data/common_shapes"
python3 -c "
import urllib.request, zipfile, os, shutil

url = 'https://github.com/alecjacobson/common-3d-test-models/archive/refs/heads/master.zip'
zip_path = 'data/common_shapes_temp.zip'
output_dir = 'data/common_shapes'
os.makedirs(output_dir, exist_ok=True)

if not os.path.exists(zip_path):
    print(f'Downloading from {url}...')
    urllib.request.urlretrieve(url, zip_path)
    print('Extracting...')
    with zipfile.ZipFile(zip_path, 'r') as z:
        z.extractall('data/')
    extracted = 'data/common-3d-test-models-master'
    if os.path.exists(extracted):
        for item in os.listdir(extracted):
            src = os.path.join(extracted, item)
            dst = os.path.join(output_dir, item)
            if not os.path.exists(dst):
                shutil.move(src, dst)
        os.rmdir(extracted)
    os.remove(zip_path)
    print('Done!')
else:
    print('Already downloaded')
"

echo ""
echo "=== Available meshes ==="
find data/common_shapes -name "*.obj" 2>/dev/null | wc -l
echo "meshes found"

echo ""
echo "Download complete!"
