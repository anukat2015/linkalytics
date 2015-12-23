
if ! [ -d ${HOME}/miniconda ]; then
    wget http://repo.continuum.io/miniconda/Miniconda-latest-Linux-x86_64.sh -O miniconda.sh
    bash miniconda.sh -b -p ${HOME}/miniconda
    conda update --yes conda
fi
