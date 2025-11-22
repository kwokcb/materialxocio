## OCIO Utilities for MaterialX

This site contains a set of utilities for working with OpenColorIO and MaterialX. The utilities are written in Python and are designed to be used as standalone scripts or as part of a larger pipeline.

Note that Functional Nodegraph generation is currently in it's early stages pending the result of `NanoColor` support.

### Repository

The <code>Github</code> repository is available <a href="https://github.com/kwokcb/materialxocio">here</a>

### Installation

To install the utilities, clone the repository and run the following command:

```bash
pip install .
```

The distribution will be available on PyPi in the near future as `materialxocio`.

### Dependencies

The utilities have the following minimal dependencies:

- OpenColorIO 2.2 and above
- MaterialX 1.38.9 and above

The latest version tested with is MaterialX 1.39.5 (development) and OpenColorIO 2.5.0 (release)

### Command Line Utilities

The repository contains the following command line utilities:

- generateOCIODefinitions: Generates MaterialX node definitions from the default ACES Cg config for 
color transforms without LUTs. Each transform is from the source colorspace to lin_rec709. 
- If source code implementations are generated, each definition consists of:
  - A node definition MaterialX file
  - A node implementation MaterialX file
  - Source code in the GLSL shading language. Note that options to use other OCIO
    provided languages can be added.
- If node graph implementations are generate, then a single file consisting of:
  - A `nodedef` 
  - A functional `nodegraph` with reference to the `nodedef` interface.

### Build

There are basic build scripts in the <a href="https://github.com/kwokcb/materialxocio/tree/main/utilities/README.md">utilities</a> folder.

### Documentation 

#### API

API documentation can be found <a href="https://kwokcb.github.io/materialxocio/docs/html/index.html">here</a>

#### Notebooks

A background describing the usage of the OCIO package can be found <a href="https://kwokcb.github.io/materialxocio/docs/mtlx_ocio.html">here</a>
