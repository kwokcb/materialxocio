# TODO: Convert README.md to index.html via script
cp README.html index.html
cd docs
echo "Install Jupyter..."
pip install jupyter --quiet
echo "Build notebooks..."
python -m jupyter execute --inplace mtlx_ocio.ipynb  > notebook_log.txt 2>&1
python -m jupyter nbconvert mtlx_ocio.ipynb  --to html 
python -m jupyter nbconvert mtlx_ocio.ipynb  --to python 
echo "Build Doxygen..."
doxygen Doxyfile > doxygen_log.txt 2>&1
cd ..