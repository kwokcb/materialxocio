echo "Build Examples..."
pushd .
cd src/materialxocio
python genOCIODefinitions.py -o ./data
python genOCIODefinitions.py -g -o ./data
popd