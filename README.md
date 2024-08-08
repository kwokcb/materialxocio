## OCIO Utilities for MaterialX

This site contains a set of utilities for working with OpenColorIO and MaterialX. The utilities are written in Python and are designed to be used as standalone scripts or as part of a larger pipeline.

### Repository

The <code>Github</code> repository is available <a href="https://github.com/kwokcb/materialxocio">here</a>

### Installation

To install the utilities, clone the repository and run the following command:

```bash
pip install .
```

The distribution will be available on PyPi in the near future as `materialxocio`

### Dependencies

The utilities require the following dependencies:

- OpenColorIO 2.2 and above
- MaterialX 1.38.9 and above

### Command Line Utilities

The repository contains the following command line utilities:

- generateOCIODefinitions: Generates MaterialX node definitions from the default ACES Cg config for 
color transforms without LUTs. Each transform is from the source colorspace to lin_rec709. Each definition consists of:
  - A node definition MaterialX file
  - A node implementation MaterialX file
  - Source code in the GLSL shading language. Note that options to use other OCIO
    provided languages can be added.

### Documentation 

#### API

API documentation can be found <a href="https://kwokcb.github.io/materialxocio/docs/html/index.html">here</a>

#### Notebooks

A background describing the usage of the OCIO package can be found <a href="https://kwokcb.github.io/materialxocio/docs/mtlx_ocio.html">here</a>
