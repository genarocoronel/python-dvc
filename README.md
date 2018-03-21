
| Linux & Mac OS | Windows | Code quality | Unit-tests |
|-------------|---------------|--------------|------------|
|[![Build Status](https://travis-ci.org/dataversioncontrol/dvc.svg?branch=master)](https://travis-ci.org/dataversioncontrol/dvc)|[![Build status](https://ci.appveyor.com/api/projects/status/rnqygb4rp1tsjvhb/branch/master?svg=true)](https://ci.appveyor.com/project/dataversioncontrol/dvc/branch/master)|[![Code Climate](https://codeclimate.com/github/dataversioncontrol/dvc/badges/gpa.svg)](https://codeclimate.com/github/dataversioncontrol/dvc)|[![Test Coverage](https://codeclimate.com/github/dataversioncontrol/dvc/badges/coverage.svg)](https://codeclimate.com/github/dataversioncontrol/dvc)|

Data Version Control or DVC is an open source tool for data science projects. 
It helps data scientists manage their code and data together in a simple form of Git-like commands.

# Get started

|Step|Command|
|----|-------|
|Track code and data together|`$ git add train.py` <br /> `$ dvc add images.zip` |
|Connect code and data by commands| `$ dvc run -d images.zip -o images/ unzip -q images.zip` <br /> `$ dvc run -d images/ -d train.py -o model.p python train.py` |
|Make changes and reproduce|`$ vi train.py` <br /> `$ dvc repro` |
|Share code|`$ git add .` <br /> `$ git commit -m 'The baseline model'` <br />  `$ git push`|
|Share data and ML models|`$ dvc config AWS.StoragePath mybucket/image_cnn` <br/> `$ dvc push`|

See more in [tutorial](https://blog.dataversioncontrol.com/data-version-control-tutorial-9146715eda46).

# Installation

## Packages

Operating system dependent packages are the recommended way to install DVC.
The latest version of the packages can be found at GitHub releases page: https://github.com/dataversioncontrol/dvc/releases

## Python Pip

DVC could be installed via the Python Package Index (PyPI).

```bash
pip install dvc
```

# Links

Website: https://dataversioncontrol.com

Tutorial: https://blog.dataversioncontrol.com/data-version-control-tutorial-9146715eda46

Documentation: http://dataversioncontrol.com/docs/

Discussion: https://discuss.dataversioncontrol.com/

# How DVC works

![how_dvc_works](https://s3-us-west-2.amazonaws.com/dvc-share/images/0.9/how_dvc_works.png)

# Copyright

This project is distributed under the Apache license version 2.0 (see the LICENSE file in the project root).

By submitting a pull request for this project, you agree to license your contribution under the Apache license version 2.0 to this project.

