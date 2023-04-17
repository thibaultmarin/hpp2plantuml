"""hpp2plantuml module

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

    usage: hpp2plantuml [-h] -i HEADER-FILE [-o FILE] [-d] [-t JINJA-FILE]
                        [--version]

    hpp2plantuml tool.

    optional arguments:
      -h, --help            show this help message and exit
      -i HEADER-FILE, --input-file HEADER-FILE
                            input file (must be quoted when using wildcards)
      -o FILE, --output-file FILE
                            output file
      -d, --enable-dependency
                            Extract dependency relationships from method arguments
      -t JINJA-FILE, --template-file JINJA-FILE
                            path to jinja2 template file
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

To customize the output PlantUML file, templates can be used (using the ``-t``
parameter):

.. code:: sh
    :name: usage-sh-template

    hpp2plantuml -i File_1.hpp -i "include/Helper_*.hpp" -o output.puml -t template.puml

This will use the ``template.puml`` file as template.  Templates follow the `jinja <http://jinja.pocoo.org/>`_
syntax.  For instance, to add a preamble to the PlantUML output, the template
file may contain:

::

    {% extends 'default.puml' %}

    {% block preamble %}
    title "This is a title"
    skinparam backgroundColor #EEEBDC
    skinparam handwritten true
    {% endblock %}

This will inherit from the default template and override the preamble only.

Module
~~~~~~

To use as a module, simply ``import hpp2plantuml``.  The ``CreatePlantUMLFile``
function can then be used to create a PlantUML file from a set of input files.
Alternatively, the ``Diagram`` object can be used directly to build internal
objects (from files or strings).  The ``Diagram.render()`` method can be used to
produce a string output instead of writing to a text file.  See the API
documentation for more details.

"""

__title__ = "hpp2plantuml"
__description__ = "Convert C++ header files to PlantUML"
__version__ = '0.8.4'
__uri__ = "https://github.com/thibaultmarin/hpp2plantuml"
__doc__ = __description__ + " <" + __uri__ + ">"
__author__ = "Thibault Marin"
__email__ = "thibault.marin@gmx.com"
__license__ = "MIT"
__copyright__ = "Copyright (c) 2023 Thibault Marin"

from .hpp2plantuml import CreatePlantUMLFile, Diagram

__all__ = ['CreatePlantUMLFile', 'Diagram']
