.. hpp2plantuml documentation master file.

hpp2plantuml documentation
==========================

.. toctree::
   :maxdepth: 4

.. _sec-intro:

Motivation
----------

The purpose of this tool is to convert C++ header files to a UML representation
in `PlantUML <https://plantuml.com>`_ syntax that can be used to generate diagrams with PlantUML.

`PlantUML <https://plantuml.com>`_ is a program rendering UML diagrams from plain text inputs using an
expressive language.

This package generates the text input to PlantUML from C++ header files.  Its
ambition is limited but it should produce reasonable conversion for simple class
hierarchies.  It aims at supporting:

- class members with properties (``private``, ``method``, ``protected``), methods with
  basic qualifiers (``static``, abstract),

- inheritance relationships,

- aggregation relationships (very basic support).

The package relies on the `CppHeaderParser <http://senexcanis.com/open-source/cppheaderparser/>`_ package for parsing of C++ header
files.


.. _sec-module-usage:

Usage
-----

The ``hpp2plantuml`` package can be used from the command line or as a module in
other applications.

Command line
~~~~~~~~~~~~

The command line usage is (``hpp2plantuml --help``):


::

    usage: hpp2plantuml [-h] -i HEADER-FILE [-o FILE] [-t JINJA-FILE] [--version]

    hpp2plantuml tool.

    optional arguments:
      -h, --help            show this help message and exit
      -i HEADER-FILE, --input-file HEADER-FILE
                            input file (must be quoted when using wildcards)
      -o FILE, --output-file FILE
                            output file
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


Module documentation generated from docstrings
----------------------------------------------

:doc:`hpp2plantuml`

Full org-mode package documentation
-----------------------------------

:doc:`org-doc`

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
