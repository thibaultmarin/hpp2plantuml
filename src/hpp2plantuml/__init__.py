""" hpp2plantuml module

.. _sec-module:

Module source code
------------------

The package relies on a layer of objects used as intermediate between the parsed
header files (parsed using ``CppHeaderParser``) and the text output for use with
PlantUML.

The main entry point () takes as input a list of header
files and creates a object from it, which contains the internal object
representation extracted jointly from the input files.

Objects for different types (e.g. class, struct, etc.) are initialized at
instantiation time from the parsed header via the ``parse_members`` method.
Conversion to text input in PlantUML syntax is performed by the ``render`` method.

Relationships between objects are extracted from a ``Diagram`` object by listing
inheritance properties and parsing member types into .


.. _sec-module-usage:

Usage
-----

The ``hpp2plantuml`` package can be used from the command line or as a module in
other applications.

Command line
~~~~~~~~~~~~

The command line usage is (``hpp2plantuml --help``):


::

    usage: hpp2plantuml [-h] -i HEADER-FILE [-o FILE] [--version]

    hpp2plantuml tool.

    optional arguments:
      -h, --help            show this help message and exit
      -i HEADER-FILE, --input-file HEADER-FILE
                            input file (must be quoted when using wildcards)
      -o FILE, --output-file FILE
                            output file
      --version             show program's version number and exit


Input files are added using the ``-i`` option.  Inputs can be full file paths or
include wildcards.  Note that double quotes are required when using wildcards.
The output file is selected with the ``-o`` option.  The output is a text file
following the PlantUML syntax.

For instance, the following command will generate an input file for PlantUML
(``output.puml``) from several header files.

.. code:: sh
    :name: usage-sh

    hpp2plantuml -i File_1.hpp -i "include/Helper_*.hpp" -o output.puml

Module
~~~~~~

To use as a module, simply ``import hpp2plantuml``.  The ``CreatePlantUMLFile``
function can then be used to create a PlantUML file from a set of input files.
Alternatively, the ``Diagram`` object can be used directly to build internal
objects (from files or strings).  The ``Diagram.render()`` method can be used to
produce a string output instead of writing to a text file.

"""

__title__ = "hpp2plantuml"
__description__ = "Convert C++ header files to PlantUML"
__version__ = '0.4'
__uri__ = "https://github.com/thibaultmarin/hpp2plantuml"
__doc__ = __description__ + " <" + __uri__ + ">"
__author__ = "Thibault Marin"
__email__ = "thibault.marin@gmx.com"
__license__ = "MIT"
__copyright__ = "Copyright (c) 2016 Thibault Marin"

from .hpp2plantuml import CreatePlantUMLFile, Diagram

__all__ = ['CreatePlantUMLFile', 'Diagram']
