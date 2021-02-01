===================================================
hpp2plantuml - Convert C++ header files to PlantUML
===================================================

    :Author: Thibault Marin
    :Date: <2016-11-30 Wed>

This is the documentation for the ``hpp2plantuml`` package, fully contained within
this single org-file.

The current version of the code is:

::
    :name: hpp2plantuml-version

    0.7.1


The source code can be found on GitHub:
`https://github.com/thibaultmarin/hpp2plantuml <https://github.com/thibaultmarin/hpp2plantuml>`_.

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

- dependency relationships

The package relies on the `CppHeaderParser <https://pypi.org/project/robotpy-cppheaderparser/>`_ package for parsing of C++ header
files.

License
-------

The license adopted for this project is the MIT license.

::

    :name: license


    The MIT License (MIT)

    Copyright (c) 2016 T

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in
    all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
    THE SOFTWARE.

Requirements
------------

This module has mostly standard dependencies; the only exception is the
`CppHeaderParser <https://pypi.org/project/robotpy-cppheaderparser/>`_ module used to parse header files.

.. table:: List of dependencies.
    :name: py-dependency-list

    +-------------------------+-----------------+
    | argparse                | argparse        |
    +-------------------------+-----------------+
    | robotpy-cppheaderparser | CppHeaderParser |
    +-------------------------+-----------------+
    | jinja2                  | jinja2          |
    +-------------------------+-----------------+

The full list of non-standard dependencies is produced by the following source
block (returning either imports or a dependency list used in `sec-package-setup-py`_):

.. code:: common-lisp
    :name: py-dependencies

    (cond
     ((string= output "import")
      (mapconcat
       (lambda (el) (concat "import " (cadr el))) dep-list "\n"))
     ((string= output "requirements")
      (concat "["
              (mapconcat
               (lambda (el) (concat "'" (car el) "'")) dep-list ", ")
              "]")))

.. code:: python
    :name: py-imports

    # %% Imports

    import os
    import re
    import glob
    import argparse
    import CppHeaderParser
    import jinja2

The tests rely on the `nosetest <http://nose.readthedocs.io/en/latest/>`_ framework and the package documentation is built
with `Sphinx <http://sphinx-doc.org>`_.

.. _sec-module:

Module source code
------------------

The package relies on a layer of objects used as intermediate between the parsed
header files (parsed using ``CppHeaderParser``) and the text output for use with
PlantUML.

The main entry point (`sec-module-create-uml`_) takes as input a list of header
files and creates a `sec-module-diagram`_ object from it, which contains the internal object
representation extracted jointly from the input files.

Objects for different types (e.g. class, struct, etc.) are initialized at
instantiation time from the parsed header via the ``parse_members`` method.
Conversion to text input in PlantUML syntax is performed by the ``render`` method.

Relationships between objects are extracted from a ``Diagram`` object by listing
inheritance properties and parsing member types into `sec-module-relationship`_.

.. _sec-module-constants:

String representation constants
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Some constant variables are defined to store the PlantUML string representation
of elementary properties and links.

- The ``MEMBER_PROP_MAP`` variable maps class member types to corresponding
  PlantUML characters.

- The ``LINK_TYPE_MAP`` variable stores the PlantUML representation of inheritance
  and aggregation relationships.

- ``CONTAINER_TYPE_MAP`` associates object types with internal classes used for
  their representation.

.. code:: python
    :name: py-constants

    # %% Constants


    # Association between member property and PlantUML symbol
    MEMBER_PROP_MAP = {
        'private': '-',
        'public': '+',
        'protected': '#'
    }

    # Links
    LINK_TYPE_MAP = {
        'inherit': '<|--',
        'aggregation': 'o--',
        'composition': '*--',
        'dependency': '<..'
    }

    # Association between object names and objects
    # - The first element is the object type name in the CppHeader object
    # - The second element is the iterator used to loop over objects
    # - The third element is a function returning the corresponding internal object
    CONTAINER_TYPE_MAP = [
        ['classes', lambda objs: objs.items(), lambda obj: Class(obj)],
        ['enums', lambda objs: objs, lambda obj: Enum(obj)]
    ]

Objects
~~~~~~~

C++ objects parsed by the ``CppHeaderParser`` module are converted to internal
objects which perform two tasks:

1. extract properties supported by PlantUML,

2. generate text following the PlantUML syntax representing the object.

The module currently supports ``class`` and ``enum`` objects.  They are implemented
via the internal ``Class`` and ``Enum`` objects, which inherits from a common base
class.

.. _sec-module-container:

Base class
^^^^^^^^^^

C++ objects are represented by objects derived from the base ``Container`` class.
The ``Container`` class is abstract and contains:

- the container type (``class``, ``enum``, ``struct`` objects are handled as ``class``
  objects),

- the object name,

- a list of members (e.g. class variable or method for a class object),

- a ``parse_members`` method which can build the list of members from a parsed
  header,

- a ``render`` method with renders the object to text, including the object
  definition (e.g. "class TestClass") and its members (e.g. member variables and
  methods).

.. code:: python
    :name: py-obj-container

    # %% Base classes


    class Container(object):
        """Base class for C++ objects

        This class defines the basic interface for parsed objects (e.g. class).
        """
        def __init__(self, container_type, name):
            """Class constructor

            Parameters
            ----------
            container_type : str
                String representation of container type (``class``, ``struct`` or
                ``enum``)
            name : str
                Object name (with ``<``, ``>`` characters removed)
            """
            self._container_type = container_type
            self._name = re.sub('[<>]', '', name)
            self._member_list = []
            self._namespace = None

        def get_name(self):
            """Name property accessor

            Returns
            -------
            str
                Object name
            """
            return self._name

        def parse_members(self, header_container):
            """Initialize object from header

            Extract object from CppHeaderParser dictionary representing a class, a
            struct or an enum object.  This extracts the namespace.  Use the
            ``parent`` field to determine is the ``namespace`` description from
            ``CppHeaderParser`` is a parent object (e.g. class) or a proper
            ``namespace``.

            Parameters
            ----------
            header_container : CppClass or CppEnum
                Parsed header for container
            """
            namespace = header_container.get('namespace', None)
            if namespace:
                if not header_container.get('parent', None):
                    self._namespace = _cleanup_namespace(namespace)
            self._do_parse_members(header_container)

        def _do_parse_members(self, header_container):
            """Initialize object from header (abstract method)

            Extract object from CppHeaderParser dictionary representing a class, a
            struct or an enum object.

            Parameters
            ----------
            header_container : CppClass or CppEnum
                Parsed header for container
            """
            raise NotImplementedError(
                'Derived class must implement :func:`_do_parse_members`.')

        def render(self):
            """Render object to string

            Returns
            -------
            str
                String representation of object following the PlantUML syntax
            """
            container_str = self._render_container_def() + ' {\n'
            for member in self._member_list:
                container_str += '\t' + member.render() + '\n'
            container_str += '}\n'
            if self._namespace is not None:
                return wrap_namespace(container_str, self._namespace)
            return container_str

        def comparison_keys(self):
            """Order comparison key between `ClassRelationship` objects

            Use the parent name, the child name then the link type as successive
            keys.

            Returns
            -------
            list
                `operator.attrgetter` objects for successive fields used as keys
            """
            return self._container_type, self._name

        def sort_members(self):
            """Sort container members

            sort the list of members by type and name
            """
            self._member_list.sort(key=lambda obj: obj.comparison_keys())

        def _render_container_def(self):
            """String representation of object definition

            Return the definition line of an object (e.g. "class MyClass").

            Returns
            -------
            str
                Container type and name as string
            """
            return self._container_type + ' ' + self._name

Members of ``Container`` objects (e.g. class member variable) are inherited from
the ``ContainerMember`` class.  The interface only includes a ``render`` method
returning a string representation of the member.  The base class
``ContainerMember`` defines this method abstract.

.. code:: python
    :name: py-obj-container-member

    # %% Object member


    class ContainerMember(object):
        """Base class for members of `Container` object

        This class defines the basic interface for object members (e.g. class
        variables, etc.)
        """
        def __init__(self, header_member, **kwargs):
            """Constructor

            Parameters
            ----------
            header_member : str
                Member name
            """
            self._name = header_member
            self._type = None

        def render(self):
            """Render object to string (abstract method)

            Returns
            -------
            str
                String representation of object member following the PlantUML
                syntax
            """
            raise NotImplementedError('Derived class must implement `render`.')

        def comparison_keys(self):
            """Order comparison key between `ClassRelationship` objects

            Use the parent name, the child name then the link type as successive
            keys.

            Returns
            -------
            list
                `operator.attrgetter` objects for successive fields used as keys
            """
            if self._type is not None:
                return self._type, self._name
            else:
                return self._name

Classes
^^^^^^^

C++ class objects are represented using the ``Class`` class.  It extends the
`sec-module-container`_ class adding class properties (template, abstract) and a list of
parent classes.  It also offers a method to extract the types of its members,
which is used to determine aggregation relationships between classes.

.. code:: python
    :name: py-render-classes

    # %% Class object


    class Class(Container):
        """Representation of C++ class

        This class derived from `Container` specializes the base class to handle
        class definition in C++ headers.

        It supports:

        * abstract and template classes
        * member variables and methods (abstract and static)
        * public, private, protected members (static)
        """
        def __init__(self, header_class):
            """Constructor

            Extract the class name and properties (template, abstract) and
            inheritance.  Then, extract the class members from the header using the
            :func:`parse_members` method.

            Parameters
            ----------
            header_class : list (str, CppClass)
                Parsed header for class object (two-element list where the first
                element is the class name and the second element is a CppClass
                object)
            """
            super().__init__(header_class[1]['declaration_method'], header_class[0])
            self._abstract = header_class[1]['abstract']
            self._template_type = None
            if 'template' in header_class[1]:
                self._template_type = _cleanup_single_line(
                    header_class[1]['template'])
            self._inheritance_list = [re.sub('<.*>', '', parent['class'])
                                      for parent in header_class[1]['inherits']]
            self.parse_members(header_class[1])

        def _do_parse_members(self, header_class):
            """Initialize class object from header

            This method extracts class member variables and methods from header.

            Parameters
            ----------
            header_class : CppClass
                Parsed header for class
            """
            member_type_map = [
                ['properties', ClassVariable],
                ['methods', ClassMethod]
            ]
            for member_type, member_type_handler in member_type_map:
                for member_prop in MEMBER_PROP_MAP.keys():
                    member_list = header_class[member_type][member_prop]
                    for header_member in member_list:
                        if not header_member.get('deleted', False):
                            self._member_list.append(
                                member_type_handler(header_member, member_prop))

        def build_variable_type_list(self):
            """Get type of member variables

            This function extracts the type of each member variable.  This is used
            to list aggregation relationships between classes.

            Returns
            -------
            list(str)
                List of types (as string) for each member variable
            """
            variable_type_list = []
            for member in self._member_list:
                if isinstance(member, ClassVariable):
                    variable_type_list.append(member.get_type())
            return variable_type_list

        def build_inheritance_list(self):
            """Get inheritance list

            Returns
            -------
            list(str)
                List of class names the current class inherits from
            """
            return self._inheritance_list

        def _render_container_def(self):
            """Create the string representation of the class

            Return the class name with template and abstract properties if
            present.  The output string follows the PlantUML syntax.  Note that
            ``struct`` and ``union`` types are rendered as ``classes``.

            Returns
            -------
            str
                String representation of class
            """
            if self._container_type in ['struct', 'union']:
                container_type = 'class'
            else:
                container_type = self._container_type
            class_str = container_type + ' ' + self._name
            if self._abstract:
                class_str = 'abstract ' + class_str
            if self._template_type is not None:
                class_str += ' <{0}>'.format(self._template_type)
            return class_str

.. _sec-module-class-member:

Class members
^^^^^^^^^^^^^

Members of C++ classes are represented by the ``ClassMember`` object, which
inherits from the base `sec-module-container`_ class.  The ``ClassMember`` class is a
super-class for `sec_class_properties`_ and `sec_class_methods`_.

In addition to the base representation, ``ClassMember`` objects store the type of
the object, the scope (e.g. public or private) and a static flag.  The rendering
of the member is mostly common between variables and methods.  The ``ClassMember``
class provides the common rendering and relies on child classes implementing the
``_render_name`` method for specialization.

.. code:: python
    :name: py-obj-class_member

    # %% Class member


    class ClassMember(ContainerMember):
        """Class member (variable and method) representation

        This class is the base class for class members.  The representation
        includes the member type (variable or method), name, scope (``public``,
        ``private`` or ``protected``) and a static flag.

        """
        def __init__(self, class_member, member_scope='private'):
            """Constructor

            Parameters
            ----------
            class_member : CppVariable or CppMethod
                Parsed member object (variable or method)
            member_scope : str
                Member scope property: ``public``, ``private`` or ``protected``
            """
            super().__init__(class_member['name'])
            self._type = None
            self._static = class_member['static']
            self._scope = member_scope
            self._properties = []

        def render(self):
            """Get string representation of member

            The string representation is with the scope indicator and a static
            keyword when the member is static.  It is postfixed by the type (return
            type for class methods) and additional properties (e.g. ``const``
            methods are flagged with the ``query`` property).  The inner part of
            the returned string contains the variable name and signature for
            methods.  This is obtained using the :func:`_render_name` method.

            Returns
            -------
            str
                String representation of member

            """
            if len(self._properties) > 0:
                props = ' {' + ', '.join(self._properties) + '}'
            else:
                props = ''
            vis = MEMBER_PROP_MAP[self._scope] + \
                  ('{static} ' if self._static else '')
            member_str = vis + self._render_name() + \
                         (' : ' + self._type if self._type else '') + \
                         props
            return member_str

        def _render_name(self):
            """Get member name

            By default (for member variables), this returns the member name.
            Derived classes can override this to control the name rendering
            (e.g. add the function prototype for member functions)
            """
            return self._name

.. _sec_class_properties:

Properties
::::::::::

The specialization required for class member variables is minimal: the member
type is extracted from the parsed dictionary, and the rest of the setup is left
to the `sec-module-class-member`_.

.. code:: python
    :name: py-obj-class_variable

    # %% Class variable


    class ClassVariable(ClassMember):
        """Object representation of class member variables

        This class specializes the `ClassMember` object for member variables.
        Additionally to the base class, it stores variable types as strings.  This
        is used to establish aggregation relationships between objects.
        """
        def __init__(self, class_variable, member_scope='private'):
            """Constructor

            Parameters
            ----------
            class_variable : CppVariable
                Parsed class variable object
            member_scope : str
                Scope property to member variable
            """
            assert(isinstance(class_variable,
                              CppHeaderParser.CppHeaderParser.CppVariable))

            super().__init__(class_variable, member_scope)

            self._type = _cleanup_type(class_variable['type'])

        def get_type(self):
            """Variable type accessor

            Returns
            -------
            str
                Variable type as string
            """
            return self._type

.. _sec_class_methods:

Methods
:::::::

Member methods store additional information on the class members: an abstract
flag is used for purely virtual methods, the method name is modified to add a
tilde sign (``~``) prefix for destructor methods and a list of parameters is
stored.

The name rendering includes the method signature.  An option to shorten the list
of parameters by keeping only types or variable names or using ellipsis may be
implemented in the future.

.. code:: python
    :name: py-obj-class_method

    # %% Class method


    class ClassMethod(ClassMember):
        """Class member method representation

        This class extends `ClassMember` for member methods.  It stores additional
        method properties (abstract, destructor flag, input parameter types).
        """
        def __init__(self, class_method, member_scope):
            """Constructor

            The method name and additional properties are extracted from the parsed
            header.

            * A list of parameter types is stored to retain the function signature.
            * The ``~`` character is appended to destructor methods.
            * ``const`` methods are flagged with the ``query`` property.

            Parameters
            ----------
            class_method : CppMethod
                Parsed class member method
            member_scope : str
                Scope of the member method

            """
            assert(isinstance(class_method,
                              CppHeaderParser.CppHeaderParser.CppMethod))

            super().__init__(class_method, member_scope)

            self._type = _cleanup_type(class_method['returns'])
            if class_method['returns_pointer']:
                self._type += '*'
            elif class_method['returns_reference']:
                self._type += '&'
            self._abstract = class_method['pure_virtual']
            if class_method['destructor']:
                self._name = '~' + self._name
            if class_method['const']:
                self._properties.append('query')
            self._param_list = []
            for param in class_method['parameters']:
                self._param_list.append([_cleanup_type(param['type']),
                                         param['name']])

        def _render_name(self):
            """Internal rendering of method name

            This method extends the base :func:`ClassMember._render_name` method by
            adding the method signature to the returned string.

            Returns
            -------
            str
                The method name (prefixed with the ``abstract`` keyword when
                appropriate) and signature
            """
            assert(not self._static or not self._abstract)

            method_str = ('{abstract} ' if self._abstract else '') + \
                         self._name + '(' + \
                         ', '.join(' '.join(it).strip()
                                   for it in self._param_list) + ')'

            return method_str

Enumeration lists
^^^^^^^^^^^^^^^^^

The ``Enum`` class representing enumeration object is a trivial extension of the
base `sec-module-container`_ class.  Note that the enumeration elements are rendered without
the actual values.

.. code:: python
    :name: py-render-enums

    # %% Enum object


    class Enum(Container):
        """Class representing enum objects

        This class defines a simple object inherited from the base `Container`
        class.  It simply lists enumerated values.
        """
        def __init__(self, header_enum):
            """Constructor

            Parameters
            ----------
            header_enum : CppEnum
                Parsed CppEnum object
            """
            super().__init__('enum', header_enum.get('name', 'empty'))
            self.parse_members(header_enum)

        def _do_parse_members(self, header_enum):
            """Extract enum values from header

            Parameters
            ----------
            header_enum : CppEnum
                Parsed `CppEnum` object
            """
            for value in header_enum.get('values', []):
                self._member_list.append(EnumValue(value['name']))


    class EnumValue(ContainerMember):
        """Class representing values in enum object

        This class only contains the name of the enum value (the actual integer
        value is ignored).
        """
        def __init__(self, header_value, **kwargs):
            """Constructor

            Parameters
            ----------
            header_value : str
                Name of enum member
            """
            super().__init__(header_value)

        def render(self):
            """Rendering to string

            This method simply returns the variable name

            Returns
            -------
            str
                The enumeration element name
            """
            return self._name

.. _sec-module-relationship:

Class relationships
^^^^^^^^^^^^^^^^^^^

The current version only supports inheritance and aggregation relationships.  No
attempt is made to differentiate between composition and aggregation
relationships from the code; instead, an object having a member of a type
defined by another class is assumed to correspond to an aggregation
relationship.

The base ``ClassRelationship`` class defines the common properties of class
relationships: a parent, a child and a connection type.  All are saved as
strings and the text representation of a connection link is obtained from the
`sec-module-constants`_.

.. code:: python
    :name: py-class_relationship

    # %% Class connections


    class ClassRelationship(object):
        """Base object for class relationships

        This class defines the common structure of class relationship objects.
        This includes a parent/child pair and a relationship type (e.g. inheritance
        or aggregation).
        """
        def __init__(self, link_type, c_parent, c_child, flag_use_namespace=False):
            """Constructor

            Parameters
            ----------
            link_type : str
                Relationship type: ``inherit`` or ``aggregation``
            c_parent : str
                Name of parent class
            c_child : str
                Name of child class
            """
            self._parent = c_parent.get_name()
            self._child = c_child.get_name()
            self._link_type = link_type
            self._parent_namespace = c_parent._namespace or None
            self._child_namespace = c_child._namespace or None
            self._flag_use_namespace = flag_use_namespace

        def comparison_keys(self):
            """Order comparison key between `ClassRelationship` objects

            Compare alphabetically based on the parent name, the child name then
            the link type.

            Returns
            -------
            list
                `operator.attrgetter` objects for successive fields used as keys
            """
            return self._parent, self._child, self._link_type

        def _render_name(self, class_name, class_namespace, flag_use_namespace):
            """Render class name with namespace prefix if necessary

            Parameters
            ----------
            class_name : str
               Name of the class
            class_namespace : str
                Namespace or None if the class is defined in the default namespace
            flag_use_namespace : bool
                When False, do not use the namespace

            Returns
            -------
            str
                Class name with appropriate prefix for use with link rendering
            """
            if not flag_use_namespace:
                return class_name

            if class_namespace is None:
                prefix = '.'
            else:
                prefix = class_namespace + '.'
            return prefix + class_name

        def render(self):
            """Render class relationship to string

            This method generically appends the parent name, a rendering of the
            link type (obtained from the :func:`_render_link_type` method) and the
            child object name.

            Returns
            -------
            str
                The string representation of the class relationship following the
                PlantUML syntax
            """
            link_str = ''

            # Wrap the link in namespace block (if both parent and child are in the
            # same namespace)
            namespace_wrap = None
            if self._parent_namespace == self._child_namespace and \
               self._parent_namespace is not None:
                namespace_wrap = self._parent_namespace

            # Prepend the namespace to the class name
            flag_render_namespace = self._flag_use_namespace and not namespace_wrap
            parent_str = self._render_name(self._parent, self._parent_namespace,
                                           flag_render_namespace)
            child_str = self._render_name(self._child, self._child_namespace,
                                          flag_render_namespace)

            # Link string
            link_str += parent_str + ' ' + self._render_link_type() + \
                        ' ' + child_str + '\n'

            if namespace_wrap is not None:
                return wrap_namespace(link_str, namespace_wrap)
            return link_str

        def _render_link_type(self):
            """Internal representation of link

            The string representation is obtained from the `LINK_TYPE_MAP`
            constant.

            Returns
            -------
            str
                The link between parent and child following the PlantUML syntax
            """
            return LINK_TYPE_MAP[self._link_type]

Inheritance
:::::::::::

The inheritance relationship is a straightforward specialization of the base
``ClassRelationship`` class: it simply forces the link type to be the string
"inherit".

.. code:: python
    :name: py-class_inheritance

    # %% Class inheritance


    class ClassInheritanceRelationship(ClassRelationship):
        """Representation of inheritance relationships

        This module extends the base `ClassRelationship` class by setting the link
        type to ``inherit``.
        """
        def __init__(self, c_parent, c_child, **kwargs):
            """Constructor

            Parameters
            ----------
            c_parent : str
                Parent class
            c_child : str
                Derived class
            kwargs : dict
                Additional parameters passed to parent class
            """
            super().__init__('inherit', c_parent, c_child, **kwargs)

Aggregation / Composition
:::::::::::::::::::::::::

The aggregation relationship specializes the base ``ClassRelationship`` class by
using the "aggregation" or "composition" link type and adding a ``count`` field
used to add a label with the number of instances of the parent class in the
PlantUML diagram (the count is omitted when equal to one).  The difference
between aggregation and composition is mainly in the ownership of the member
variable.  A raw pointer is interpreted as an aggregation relationship while any
other container is interpreted as a composition relationship.

.. code:: python
    :name: py-class_aggregation

    # %% Class aggregation


    class ClassAggregationRelationship(ClassRelationship):
        """Representation of aggregation relationships

        This module extends the base `ClassRelationship` class by setting the link
        type to ``aggregation``.  It also keeps a count of aggregation, which is
        displayed near the arrow when using PlantUML.

        Aggregation relationships are simplified to represent the presence of a
        variable type (possibly within a container such as a list) in a class
        definition.
        """
        def __init__(self, c_object, c_container, c_count=1,
                     rel_type='aggregation', **kwargs):
            """Constructor

            Parameters
            ----------
            c_object : str
                Class corresponding to the type of the member variable in the
                aggregation relationship
            c_container : str
                Child (or client) class of the aggregation relationship
            c_count : int
                The number of members of ``c_container`` that are of type (possibly
                through containers) ``c_object``
            rel_type : str
                Relationship type: ``aggregation`` or ``composition``
            kwargs : dict
                Additional parameters passed to parent class
            """
            super().__init__(rel_type, c_object, c_container, **kwargs)
            self._count = c_count

        def _render_link_type(self):
            """Internal link rendering

            This method overrides the default link rendering defined in
            :func:`ClassRelationship._render_link_type` to include a count near the
            end of the arrow.
            """
            count_str = '' if self._count == 1 else '"%d" ' % self._count
            return count_str + LINK_TYPE_MAP[self._link_type]

Dependency
::::::::::

The dependency relationship is not directly extracted from C++ code, but it can
be manipulated when using the ``Diagram`` object.  In PlantUML, it corresponds to
the ``<..`` link type (`http://plantuml.com/class-diagram <http://plantuml.com/class-diagram>`_).

.. code:: python
    :name: py-class_dependency

    # %% Class dependency


    class ClassDependencyRelationship(ClassRelationship):
        """Dependency relationship

        Dependencies occur when member methods depend on an object of another class
        in the diagram.
        """
        def __init__(self, c_parent, c_child, **kwargs):
            """Constructor

            Parameters
            ----------
            c_parent : str
                Class corresponding to the type of the member variable in the
                dependency relationship
            c_child : str
                Child (or client) class of the dependency relationship
            kwargs : dict
                Additional parameters passed to parent class
            """
            super().__init__('dependency', c_parent, c_child, **kwargs)

.. _sec-module-diagram:

Diagram object
^^^^^^^^^^^^^^

The ``Diagram`` object is the main interface between the C++ code and the PlantUML
program.  It contains a list of objects parsed from the header files, maintains
lists of relationships and provides rendering facilities to produce a string
ready to process by PlantUML.

An example use case for the ``Diagram`` class could be:

.. code:: python
    :name: py-diag-example

    # Create object
    diag = Diagram()
    # Initialize from filename
    diag.create_from_file(filename)
    # Get output string following PlantUML syntax
    output_string = diag.render()

The interface methods and their behavior are summarized in
Table `tbl-diagram-interface`_.

.. table:: Public interface for populating a ``Diagram`` object.
    :name: tbl-diagram-interface

    +----------------------------+------------+-------------+--------+-------+--------------+
    | Method name                | input type | input list? | reset? | sort? | build lists? |
    +============================+============+=============+========+=======+==============+
    | create\_from\_file         | file       | no          | yes    | yes   | yes          |
    +----------------------------+------------+-------------+--------+-------+--------------+
    | create\_from\_file\_list   | file       | yes         | yes    | yes   | yes          |
    +----------------------------+------------+-------------+--------+-------+--------------+
    | add\_from\_file            | file       | no          | no     | no    | no           |
    +----------------------------+------------+-------------+--------+-------+--------------+
    | add\_from\_file\_list      | file       | yes         | no     | no    | no           |
    +----------------------------+------------+-------------+--------+-------+--------------+
    | create\_from\_string       | string     | no          | yes    | yes   | yes          |
    +----------------------------+------------+-------------+--------+-------+--------------+
    | create\_from\_string\_list | string     | yes         | yes    | yes   | yes          |
    +----------------------------+------------+-------------+--------+-------+--------------+
    | add\_from\_string          | string     | no          | no     | no    | no           |
    +----------------------------+------------+-------------+--------+-------+--------------+
    | add\_from\_string\_list    | string     | yes         | no     | no    | no           |
    +----------------------------+------------+-------------+--------+-------+--------------+

Functionally, parsing of the C++ headers is left to the ``CppHeaderParser``
module, the output of which is parsed into internal objects using ``Container``
parsers.  The main functionality of the ``Diagram`` class consists in building the
relationship lists between classes.  The assumption is that for a link to be
stored, it must be between two objects present in the ``Diagram`` object (no
relationships with external classes).

To build the inheritance list, the objects are browsed and
``ClassInheritanceRelationship`` instances are added to the list whenever the
parent class is defined within the ``Diagram`` object.

Construction of the list of aggregation links is slightly more complex.  A first
run through the object extracts all the member types for ``Class`` objects.  Next
a list of (type, count) pairs is constructed for members of types defined within
the ``Diagram`` object.  Finally, the list is used to instantiate
``ClassAggregationRelationship`` objects stored in a list.

The rendering function builds a string containing the PlantUML preamble and
postamble text for diagrams (``@startuml``, ``@enduml``), the rendered text for each
object and the rendered relationship links.

In order to ensure that the rendering is reproducible, a sorting mechanism has
been implemented for objects, members and relationships.  Objects and object
members are sorted by type and name and relationships are sorted by parent name,
child name and link type if necessary.  The ``add_from_*`` interface methods can
be used to avoid this sorting step.

.. code:: python
    :name: py-obj-diagram

    # %% Diagram class


    class Diagram(object):
        """UML diagram object

        This class lists the objects in the set of files considered, and the
        relationships between object.

        The main interface to the `Diagram` object is via the ``create_*`` and
        ``add_*`` methods.  The former parses objects and builds relationship lists
        between the different parsed objects.  The latter only parses objects and
        does not builds relationship lists.

        Each method has versions for file and string inputs and folder string lists
        and file lists inputs.
        """
        def __init__(self, template_file=None, flag_dep=False):
            """Constructor

            The `Diagram` class constructor simply initializes object lists.  It
            does not create objects or relationships.
            """
            self._flag_dep = flag_dep
            self.clear()
            loader_list = []
            if template_file is not None:
                loader_list.append(jinja2.FileSystemLoader(
                    os.path.abspath(os.path.dirname(template_file))))
                self._template_file = os.path.basename(template_file)
            else:
                self._template_file = 'default.puml'
            loader_list.append(jinja2.PackageLoader('hpp2plantuml', 'templates'))
            self._env = jinja2.Environment(loader=jinja2.ChoiceLoader(
                loader_list), keep_trailing_newline=True)

        def clear(self):
            """Reinitialize object"""
            self._objects = []
            self._inheritance_list = []
            self._aggregation_list = []
            self._dependency_list = []

        def _sort_list(input_list):
            """Sort list using `ClassRelationship` comparison

            Parameters
            ----------
            input_list : list(ClassRelationship)
                Sort list using the :func:`ClassRelationship.comparison_keys`
                comparison function
            """
            input_list.sort(key=lambda obj: obj.comparison_keys())

        def sort_elements(self):
            """Sort elements in diagram

            Sort the objects and relationship links.  Objects are sorted using the
            :func:`Container.comparison_keys` comparison function and list are
            sorted using the `_sort_list` helper function.
            """
            self._objects.sort(key=lambda obj: obj.comparison_keys())
            for obj in self._objects:
                obj.sort_members()
            Diagram._sort_list(self._inheritance_list)
            Diagram._sort_list(self._aggregation_list)
            Diagram._sort_list(self._dependency_list)

        def _build_helper(self, input, build_from='string', flag_build_lists=True,
                          flag_reset=False):
            """Helper function to initialize a `Diagram` object from parsed headers

            Parameters
            ----------
            input : CppHeader or str or list(CppHeader) or list(str)
                Input of arbitrary type.  The processing depends on the
                ``build_from`` parameter
            build_from : str
                Determines the type of the ``input`` variable:

                * ``string``: ``input`` is a string containing C++ header code
                * ``file``: ``input`` is a filename to parse
                * ``string_list``: ``input`` is a list of strings containing C++
                  header code
                * ``file_list``: ``input`` is a list of filenames to parse

            flag_build_lists : bool
                When True, relationships lists are built and the objects in the
                diagram are sorted, otherwise, only object parsing is performed
            flag_reset : bool
                If True, the object is initialized (objects and relationship lists
                are cleared) prior to parsing objects, otherwise, new objects are
                appended to the list of existing ones
            """
            if flag_reset:
                self.clear()
            if build_from in ('string', 'file'):
                self.parse_objects(input, build_from)
            elif build_from in ('string_list', 'file_list'):
                build_from_single = re.sub('_list$', '', build_from)
                for single_input in input:
                    self.parse_objects(single_input, build_from_single)
            if flag_build_lists:
                self.build_relationship_lists()
                self.sort_elements()

        def create_from_file(self, header_file):
            """Initialize `Diagram` object from header file

            Wrapper around the :func:`_build_helper` function, with ``file`` input,
            building the relationship lists and with object reset.
            """
            self._build_helper(header_file, build_from='file',
                               flag_build_lists=True, flag_reset=True)

        def create_from_file_list(self, file_list):
            """Initialize `Diagram` object from list of header files

            Wrapper around the :func:`_build_helper` function, with ``file_list``
            input, building the relationship lists and with object reset.
            """
            self._build_helper(file_list, build_from='file_list',
                               flag_build_lists=True, flag_reset=True)

        def add_from_file(self, header_file):
            """Augment `Diagram` object from header file

            Wrapper around the :func:`_build_helper` function, with ``file`` input,
            skipping building of the relationship lists and without object reset
            (new objects are added to the object).
            """
            self._build_helper(header_file, build_from='file',
                               flag_build_lists=False, flag_reset=False)

        def add_from_file_list(self, file_list):
            """Augment `Diagram` object from list of header files

            Wrapper around the :func:`_build_helper` function, with ``file_list``
            input, skipping building of the relationship lists and without object
            reset (new objects are added to the object).
            """
            self._build_helper(file_list, build_from='file_list',
                               flag_build_lists=False, flag_reset=False)

        def create_from_string(self, header_string):
            """Initialize `Diagram` object from header string

            Wrapper around the :func:`_build_helper` function, with ``string``
            input, building the relationship lists and with object reset.
            """
            self._build_helper(header_string, build_from='string',
                               flag_build_lists=True, flag_reset=True)

        def create_from_string_list(self, string_list):
            """Initialize `Diagram` object from list of header strings

            Wrapper around the :func:`_build_helper` function, with ``string_list``
            input, skipping building of the relationship lists and with object
            reset.
            """
            self._build_helper(string_list, build_from='string_list',
                               flag_build_lists=True, flag_reset=True)

        def add_from_string(self, header_string):
            """Augment `Diagram` object from header string

            Wrapper around the :func:`_build_helper` function, with ``string``
            input, skipping building of the relationship lists and without object
            reset (new objects are added to the object).
            """
            self._build_helper(header_string, build_from='string',
                               flag_build_lists=False, flag_reset=False)

        def add_from_string_list(self, string_list):
            """Augment `Diagram` object from list of header strings

            Wrapper around the :func:`_build_helper` function, with ``string_list``
            input, building the relationship lists and without object reset (new
            objects are added to the object).
            """
            self._build_helper(string_list, build_from='string_list',
                               flag_build_lists=False, flag_reset=False)

        def build_relationship_lists(self):
            """Build inheritance and aggregation lists from parsed objects

            This method successively calls the :func:`build_inheritance_list` and
            :func:`build_aggregation_list` methods.
            """
            self.build_inheritance_list()
            self.build_aggregation_list()
            if self._flag_dep:
                self.build_dependency_list()

        def parse_objects(self, header_file, arg_type='string'):
            """Parse objects

            This method parses file of string inputs using the CppHeaderParser
            module and extracts internal objects for rendering.

            Parameters
            ----------
            header_file : str
                A string containing C++ header code or a filename with C++ header
                code
            arg_type : str
                It set to ``string``, ``header_file`` is considered to be a string,
                otherwise, it is assumed to be a filename
            """
            # Parse header file
            parsed_header = CppHeaderParser.CppHeader(header_file,
                                                      argType=arg_type)
            for container_type, container_iterator, \
                container_handler in CONTAINER_TYPE_MAP:
                objects = parsed_header.__getattribute__(container_type)
                for obj in container_iterator(objects):
                    self._objects.append(container_handler(obj))

        def _make_class_list(self):
            """Build list of classes

            Returns
            -------
            list(dict)
                Each entry is a dictionary with keys ``name`` (class name) and
                ``obj`` the instance of the `Class` class
            """
            return [{'name': obj.get_name(), 'obj': obj}
                    for obj in self._objects if isinstance(obj, Class)]

        def build_inheritance_list(self):
            """Build list of inheritance between objects

            This method lists all the inheritance relationships between objects
            contained in the `Diagram` object (external relationships are ignored).

            The implementation establishes a list of available classes and loops
            over objects to obtain their inheritance.  When parent classes are in
            the list of available classes, a `ClassInheritanceRelationship` object
            is added to the list.
            """
            self._inheritance_list = []
            # Build list of classes in diagram
            class_list_obj = self._make_class_list()
            class_list = [c['name'] for c in class_list_obj]
            flag_use_namespace = any([c['obj']._namespace for c in class_list_obj])

            # Create relationships

            # Inheritance
            for obj in self._objects:
                obj_name = obj.get_name()
                if isinstance(obj, Class):
                    for parent in obj.build_inheritance_list():
                        if parent in class_list:
                            parent_obj = class_list_obj[
                                class_list.index(parent)]['obj']
                            self._inheritance_list.append(
                                ClassInheritanceRelationship(
                                    parent_obj, obj,
                                    flag_use_namespace=flag_use_namespace))

        def build_aggregation_list(self):
            """Build list of aggregation relationships

            This method loops over objects and finds members with type
            corresponding to other classes defined in the `Diagram` object (keeping
            a count of occurrences).

            The procedure first builds an internal dictionary of relationships
            found, augmenting the count using the :func:`_augment_comp` function.
            In a second phase, `ClassAggregationRelationship` objects are created
            for each relationships, using the calculated count.
            """
            self._aggregation_list = []
            # Build list of classes in diagram
            # Build list of classes in diagram
            class_list_obj = self._make_class_list()
            class_list = [c['name'] for c in class_list_obj]
            flag_use_namespace = any([c['obj']._namespace for c in class_list_obj])

            # Build member type list
            variable_type_list = {}
            for obj in self._objects:
                obj_name = obj.get_name()
                if isinstance(obj, Class):
                    variable_type_list[obj_name] = obj.build_variable_type_list()
            # Create aggregation links
            aggregation_counts = {}

            for child_class in class_list:
                if child_class in variable_type_list.keys():
                    var_types = variable_type_list[child_class]
                    for var_type in var_types:
                        for parent in class_list:
                            if re.search(r'\b' + parent + r'\b', var_type):
                                rel_type = 'composition'
                                if '{}*'.format(parent) in var_type:
                                    rel_type = 'aggregation'
                                self._augment_comp(aggregation_counts, parent,
                                                   child_class, rel_type=rel_type)
            for obj_class, obj_comp_list in aggregation_counts.items():
                for comp_parent, rel_type, comp_count in obj_comp_list:
                    obj_class_idx = class_list.index(obj_class)
                    obj_class_obj = class_list_obj[obj_class_idx]['obj']
                    comp_parent_idx = class_list.index(comp_parent)
                    comp_parent_obj = class_list_obj[comp_parent_idx]['obj']
                    self._aggregation_list.append(
                        ClassAggregationRelationship(
                            obj_class_obj, comp_parent_obj, comp_count,
                            rel_type=rel_type,
                            flag_use_namespace=flag_use_namespace))

        def build_dependency_list(self):
            """Build list of dependency between objects

            This method lists all the dependency relationships between objects
            contained in the `Diagram` object (external relationships are ignored).

            The implementation establishes a list of available classes and loops
            over objects, list their methods adds a dependency relationship when a
            method takes an object as input.
            """

            self._dependency_list = []
            # Build list of classes in diagram
            class_list_obj = self._make_class_list()
            class_list = [c['name'] for c in class_list_obj]
            flag_use_namespace = any([c['obj']._namespace for c in class_list_obj])

            # Create relationships

            # Add all objects name to list
            objects_name = []
            for obj in self._objects:
                objects_name.append(obj.get_name())

            # Dependency
            for obj in self._objects:
                if isinstance(obj, Class):
                    for member in obj._member_list:
                        # Check if the member is a method
                        if isinstance(member, ClassMethod):
                            for method in member._param_list:
                                index = ValueError
                                try:
                                    # Check if the method param type is a Class
                                    # type
                                    index = [re.search(o, method[0]) is not None
                                             for o in objects_name].index(True)
                                except ValueError:
                                    pass
                                if index != ValueError and \
                                   method[0] != obj.get_name():
                                    depend_obj = self._objects[index]

                                    self._dependency_list.append(
                                        ClassDependencyRelationship(
                                            depend_obj, obj,
                                            flag_use_namespace=flag_use_namespace))

        def _augment_comp(self, c_dict, c_parent, c_child, rel_type='aggregation'):
            """Increment the aggregation reference count

            If the aggregation relationship is not in the list (``c_dict``), then
            add a new entry with count 1.  If the relationship is already in the
            list, then increment the count.

            Parameters
            ----------
            c_dict : dict
                List of aggregation relationships.  For each dictionary key, a pair
                of (str, int) elements: string and number of occurrences
            c_parent : str
                Parent class name
            c_child : str
                Child class name
            rel_type : str
                Relationship type: ``aggregation`` or ``composition``
            """
            if c_child not in c_dict:
                c_dict[c_child] = [[c_parent, rel_type, 1], ]
            else:
                parent_list = [c[:2] for c in c_dict[c_child]]
                if [c_parent, rel_type] not in parent_list:
                    c_dict[c_child].append([c_parent, rel_type, 1])
                else:
                    c_idx = parent_list.index([c_parent, rel_type])
                    c_dict[c_child][c_idx][2] += 1

        def render(self):
            """Render full UML diagram

            The string returned by this function should be ready to use with the
            PlantUML program.  It includes all the parsed objects with their
            members, and the inheritance and aggregation relationships extracted
            from the list of objects.

            Returns
            -------
            str
                String containing the full string representation of the `Diagram`
                object, including objects and object relationships
            """
            template = self._env.get_template(self._template_file)
            return template.render(objects=self._objects,
                                   inheritance_list=self._inheritance_list,
                                   aggregation_list=self._aggregation_list,
                                   dependency_list=self._dependency_list,
                                   flag_dep=self._flag_dep)

Helper functions
~~~~~~~~~~~~~~~~

This section briefly describes the helper functions defined in the module.

Sanitize strings
^^^^^^^^^^^^^^^^

The ``_cleanup_type`` function tries to unify the string representation of
variable types by eliminating spaces around ``\*`` characters.

.. code:: python
    :name: py-helper-cleanup-str

    # %% Cleanup object type string


    def _cleanup_type(type_str):
        """Cleanup string representing a C++ type

        Cleanup simply consists in removing spaces before a ``*`` character and
        preventing multiple successive spaces in the string.

        Parameters
        ----------
        type_str : str
            A string representing a C++ type definition

        Returns
        -------
        str
            The type string after cleanup
        """
        return re.sub('\s*([<>])\s*', r'\1',
                      re.sub(r'[ ]+([*&])', r'\1',
                             re.sub(r'(\s)+', r'\1', type_str)))

    def _cleanup_namespace(ns_str):
        """Cleanup string representing a C++ namespace

        Cleanup simply consists in removing leading and trailing colon characters
        (``:``), and ``<>`` blocks.

        Parameters
        ----------
        ns_str : str
            A string representing a C++ namespace

        Returns
        -------
        str
            The namespace string after cleanup
        """
        return re.sub('<([^>]+)>', r'\1',
                      re.sub('(.+)<[^>]+>', r'\1',
                             re.sub('^:+', '',
                                    re.sub(':+$', '', ns_str))))

The ``_cleanup_single_line`` function transforms a multiline input string into a
single string version.

.. code:: python
    :name: py-helper-cleanup-line

    # %% Single line version of string


    def _cleanup_single_line(input_str):
        """Cleanup string representing a C++ type

        Remove line returns

        Parameters
        ----------
        input_str : str
            A string possibly spreading multiple lines

        Returns
        -------
        str
            The type string in a single line
        """
        return re.sub(r'\s+', ' ', re.sub(r'(\r)?\n', ' ', input_str))

Expand file list
^^^^^^^^^^^^^^^^

The `sec-module-create-uml`_ accepts wildcards in filenames; they are resolved
using the ``glob`` package.  The ``expand_file_list`` function takes as input a list
of filenames and expands wildcards using the ``glob`` command returning a list of
existing filenames without wildcards.

.. code:: python
    :name: py-build-file-list

    # %% Expand wildcards in file list


    def expand_file_list(input_files):
        """Find all files in list (expanding wildcards)

        This function uses `glob` to find files matching each string in the input
        list.

        Parameters
        ----------
        input_files : list(str)
            List of strings representing file names and possibly including
            wildcards

        Returns
        -------
        list(str)
            List of filenames (with wildcards expanded).  Each element contains the
            name of an existing file
        """
        file_list = []
        for input_file in input_files:
            file_list += glob.glob(input_file, recursive=True)
        return file_list

Namespace wrapper
^^^^^^^^^^^^^^^^^

The ``wrap_namespace`` function wraps a rendered PlantUML string in a ``namespace``
block.

.. code:: python
    :name: py-help-namespace

    def wrap_namespace(input_str, namespace):
        """Wrap string in namespace

        Parameters
        ----------
        input_str : str
            String containing PlantUML code
        namespace : str
           Namespace name

        Returns
        -------
        str
            ``input_str`` wrapped in ``namespace`` block
        """
        return 'namespace {} {{\n'.format(namespace) + \
            '\n'.join([re.sub('^', '\t', line)
                       for line in input_str.splitlines()]) + \
            '\n}\n'

.. _sec-module-create-uml:

Main function: create PlantUML from C++
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``CreatePlantUMLFile`` function is the main entry point for the module.  It
takes as input a list of header files (possibly with wildcards) and an output
filename and converts the input header files into a text file ready for use with
the PlantUML program.

The function creates a ``Diagram`` object, initializes it with the expanded list
of input files and writes the content of the ``Diagram.render()`` method to the
output file.

.. code:: python
    :name: py-create-plantuml

    # %% Main function


    def CreatePlantUMLFile(file_list, output_file=None, **diagram_kwargs):
        """Create PlantUML file from list of header files

        This function parses a list of C++ header files and generates a file for
        use with PlantUML.

        Parameters
        ----------
        file_list : list(str)
            List of filenames (possibly, with wildcards resolved with the
            :func:`expand_file_list` function)
        output_file : str
            Name of the output file
        diagram_kwargs : dict
            Additional parameters passed to :class:`Diagram` constructor
        """
        if isinstance(file_list, str):
            file_list_c = [file_list, ]
        else:
            file_list_c = file_list
        diag = Diagram(**diagram_kwargs)
        diag.create_from_file_list(list(set(expand_file_list(file_list_c))))
        diag_render = diag.render()

        if output_file is None:
            print(diag_render)
        else:
            with open(output_file, 'wt') as fid:
                fid.write(diag_render)

Default template
~~~~~~~~~~~~~~~~

The rendering of the PlantUML file is managed by a ```jinja`` <http://jinja.pocoo.org/>`_ template.  The
default template is as follows:

::

    :name: jinja2-tpl

    @startuml

    {% block preamble %}
    {% endblock %}

    {% block objects %}
    /' Objects '/
    {% for object in objects %}
    {{ object.render() }}
    {% endfor %}
    {% endblock %}

    {% block inheritance %}
    /' Inheritance relationships '/
    {% for link in inheritance_list %}
    {{ link.render() }}
    {% endfor %}
    {% endblock %}

    {% block aggregation %}
    /' Aggregation relationships '/
    {% for link in aggregation_list %}
    {{ link.render() }}
    {% endfor %}
    {% endblock %}
    {% if flag_dep %}
    {% block dependency %}

    /' Dependency relationships '/
    {% for link in dependency_list %}
    {{ link.render() }}
    {% endfor %}
    {% endblock %}
    {% endif %}

    @enduml

The template successively prints the following blocks

``preamble``
    Empty by default, can be used to insert a title and PlantUML
    ``skinparam`` options

``objects``
    Classes, structs and enum objects

``inheritance``
    Inheritance links

``aggregation``
    Aggregation links

.. _sec-module-cmd:

Command line interface
~~~~~~~~~~~~~~~~~~~~~~

The ``main`` function provides a minimal command line interface using ``argparse``
to parse input arguments.  The function passes the command line arguments to the
`sec-module-create-uml`_ function.

.. code:: python
    :name: py-cmd-main

    # %% Command line interface


    def main():(ref:module-main)
        """Command line interface

        This function is a command-line interface to the
        :func:`hpp2plantuml.CreatePlantUMLFile` function.

        Arguments are read from the command-line, run with ``--help`` for help.
        """
        parser = argparse.ArgumentParser(description='hpp2plantuml tool.')
        parser.add_argument('-i', '--input-file', dest='input_files',
                            action='append', metavar='HEADER-FILE', required=True,
                            help='input file (must be quoted' +
                            ' when using wildcards)')
        parser.add_argument('-o', '--output-file', dest='output_file',
                            required=False, default=None, metavar='FILE',
                            help='output file')
        parser.add_argument('-d', '--enable-dependency', dest='flag_dep',
                            required=False, default=False, action='store_true',
                            help='Extract dependency relationships from method ' +
                            'arguments')
        parser.add_argument('-t', '--template-file', dest='template_file',
                            required=False, default=None, metavar='JINJA-FILE',
                            help='path to jinja2 template file')
        parser.add_argument('--version', action='version',
                            version='%(prog)s ' + '0.7.1')
        args = parser.parse_args()
        if len(args.input_files) > 0:
            CreatePlantUMLFile(args.input_files, args.output_file,
                               template_file=args.template_file,
                               flag_dep=args.flag_dep)

    # %% Standalone mode


    if __name__ == '__main__':
        main()

.. _sec-module-install:

Installation
------------

Using ``pip``
~~~~~~~~~~~~~

The package is available on `PyPi <https://pypi.python.org/>`_ and can be installed using pip:

::

    pip install hpp2plantuml

From source
~~~~~~~~~~~

The code uses ``setuptools``, so it can be built using:

::

    python setup.py install

To build the documentation, run:

::

    python setup.py sphinx

To run the tests, run:

::

    python setup.py test

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

Tests
-----

Testing is performed using the `nose <http://nose.readthedocs.io/en/latest/>`_ framework.  The tests are defined in the
``test_hpp2plantuml.py`` file located in the test folder.  They can be run with
the ``python setup.py test`` command.

Two types of tests are considered: small scale tests for individual components,
which are defined in org-tables (C++ source/reference output pairs) and tests on
a large input header file.

For the tests stored in org-tables, the pipe character "|" being a special
character in org-mode, it is replaced by "@" in the tables and fixed in python.

Following is the test setup code.

.. code:: python
    :name: test-setup

    """Test module for hpp2plantuml"""

    # %% Imports


    import os
    import io
    import sys
    import re
    import nose.tools as nt
    import CppHeaderParser
    import hpp2plantuml

    test_fold = os.path.abspath(os.path.dirname(__file__))

    # %% Helper functions


    def get_parsed_element(input_str):
        return CppHeaderParser.CppHeader(input_str, argType='string')


    @nt.nottest
    def fix_test_list_def(test_list):
        test_list_out = []
        for test_entry in test_list:
            test_entry_out = []
            for test_str in test_entry:
                test_entry_out.append(re.sub(u'@', '|', test_str))
            test_list_out.append(test_entry_out)
        return test_list_out

Module tests
~~~~~~~~~~~~

The module tests are not strictly speaking unit tests, as they rely on parsing
of a header file, but they aim at evaluating simple functionality of the
different modules implemented.

Container
^^^^^^^^^

The test for the ``Container`` class tests elementary functionality: members and
sorting keys.

.. code:: python
    :name: test-unit-container

    # %% Test containers


    class TestContainer:
        def test_init(self):
            c_type = "container_type"
            c_name = "container_name"
            c_obj = hpp2plantuml.hpp2plantuml.Container(c_type, c_name)
            nt.assert_equal(c_obj.get_name(), c_name)
            nt.assert_equal(c_obj.render(), 'container_type container_name {\n}\n')

        def test_comparison_keys(self):
            c_list = [
                ['class', 'ABD'],
                ['enum', 'ABDa'],
                ['class', 'abcd'],
            ]
            ref_sort_idx = [0, 2, 1]
            c_obj_list = []
            for c_type, c_name in c_list:
                c_obj_list.append(hpp2plantuml.hpp2plantuml.Container(
                    c_type, c_name))
            c_obj_list.sort(key=lambda obj: obj.comparison_keys())

            for i in range(len(c_list)):
                nt.assert_equal(c_obj_list[i].get_name(),
                                c_list[ref_sort_idx[i]][1])

Class
^^^^^

Testing for classes is performed by parsing minimal C++ code segments and
comparing the rendered text to a reference.  The input/output pairs are stored
in an org-table and tangled to test files.  Adding tests should be as simple as
adding rows to the table, with the constraint that each test should be contained
in a single row of the table.

Class variable
::::::::::::::

Class variables have simple functionality (name, type and scope).  The following
table (Table `tbl-unittest-class_var`_) defines tests that validate
the representation of variables.

.. table:: List of test segments and corresponding PlantUML strings.
    :name: tbl-unittest-class_var

    +---------------------------------------------+-------------------+
    | C++                                         | plantuml          |
    +=============================================+===================+
    | "class Test {\npublic:\nint member; };"     | "+member : int"   |
    +---------------------------------------------+-------------------+
    | "class Test {\nprivate:\nint \* member; };" | "-member : int\*" |
    +---------------------------------------------+-------------------+
    | "class Test {\nprotected:\nint &member; };" | "#member : int&"  |
    +---------------------------------------------+-------------------+


.. code:: python
    :name: test-unit-class_var

    # %% Test class variables


    class TestClassVariable:
        def test_list_entries(self):
            for test_idx, (input_str, output_ref_str) in \
                enumerate(fix_test_list_def(test_list_classvar)):
                p = get_parsed_element(input_str)
                class_name = re.sub(r'.*(class|struct)\s*(\w+).*', r'\2',
                                    input_str.replace('\n', ' '))
                class_input = [class_name, p.classes[class_name]]
                obj_c = hpp2plantuml.hpp2plantuml.Class(class_input)
                obj_m = obj_c._member_list[0]
                nt.assert_equal(output_ref_str, obj_m.render(),
                                'Test {0} failed [input: {1}]'.format(test_idx,
                                                                      input_str))

Class method
::::::::::::

The tests for class methods are listed in
Table `tbl-unittest-class_method`_.  Note that template methods are not
supported by PlantUML.

.. table:: List of test segments and corresponding PlantUML strings.
    :name: tbl-unittest-class_method

    +--------------------------------------------------------------------------------+--------------------------------------+
    | C++                                                                            | plantuml                             |
    +================================================================================+======================================+
    | "class Test {\npublic:\nint & func(int \* a); };"                              | "+func(int\* a) : int&"              |
    +--------------------------------------------------------------------------------+--------------------------------------+
    | "class Test {\npublic:\nstatic int func(int & a); };"                          | "+{static} func(int& a) : int"       |
    +--------------------------------------------------------------------------------+--------------------------------------+
    | "class Test {\nprivate:\nvirtual int \* func() const = 0; };"                  | "-{abstract} func() : int\* {query}" |
    +--------------------------------------------------------------------------------+--------------------------------------+
    | "class Test {\npublic:\n~Test(); };"                                           | "+~Test()"                           |
    +--------------------------------------------------------------------------------+--------------------------------------+
    | "class Test {\nprotected:\ntemplate <typename T>int &func(string &) const; };" | "#func(string &) : int& {query}"     |
    +--------------------------------------------------------------------------------+--------------------------------------+


.. code:: python
    :name: test-unit-class_method

    # %% Test class methods


    class TestClassMethod:
        def test_list_entries(self):
            for test_idx, (input_str, output_ref_str) in \
                enumerate(fix_test_list_def(test_list_classmethod)):
                p = get_parsed_element(input_str)
                class_name = re.sub(r'.*(class|struct)\s*(\w+).*', r'\2',
                                    input_str.replace('\n', ' '))
                class_input = [class_name, p.classes[class_name]]
                obj_c = hpp2plantuml.hpp2plantuml.Class(class_input)
                obj_m = obj_c._member_list[0]
                nt.assert_equal(output_ref_str, obj_m.render(),
                                'Test {0} failed [input: {1}]'.format(test_idx,
                                                                      input_str))

Class
:::::

The unit test for classes includes rendering tests for the code segments in
Table `tbl-unittest-class`_.  It includes templates and abstract classes.

.. table:: List of test segments and corresponding PlantUML strings.
    :name: tbl-unittest-class

    +-----------------------------------------------------------------------+---------------------------------------------------------------------------------------+
    | C++                                                                   | plantuml                                                                              |
    +=======================================================================+=======================================================================================+
    | "class Test {\nprotected:\nint & member; };"                          | "class Test {\n\t#member : int&\n}\n"                                                 |
    +-----------------------------------------------------------------------+---------------------------------------------------------------------------------------+
    | "struct Test {\nprotected:\nint & member; };"                         | "class Test {\n\t#member : int&\n}\n"                                                 |
    +-----------------------------------------------------------------------+---------------------------------------------------------------------------------------+
    | "class Test\n{\npublic:\nvirtual int func() = 0; };"                  | "abstract class Test {\n\t+{abstract} func() : int\n}\n"                              |
    +-----------------------------------------------------------------------+---------------------------------------------------------------------------------------+
    | "template <typename T> class Test{\nT* func(T& arg); };"              | "class Test <template<typename T>> {\n\t-func(T& arg) : T\*\n}\n"                     |
    +-----------------------------------------------------------------------+---------------------------------------------------------------------------------------+
    | "template <typename T> class Test{\nvirtual T\* func(T& arg)=0; };"   | "abstract class Test <template<typename T>> {\n\t-{abstract} func(T& arg) : T\*\n}\n" |
    +-----------------------------------------------------------------------+---------------------------------------------------------------------------------------+
    | "namespace Interface {\nclass Test {\nprotected:\nint & member; };};" | "namespace Interface {\n\tclass Test {\n\t\t#member : int&\n\t}\n}\n"                 |
    +-----------------------------------------------------------------------+---------------------------------------------------------------------------------------+

.. code:: python
    :name: test-unit-class

    # %% Test classes


    class TestClass:
        def test_list_entries(self):
            for test_idx, (input_str, output_ref_str) in \
                enumerate(fix_test_list_def(test_list_class)):
                p = get_parsed_element(input_str)
                class_name = re.sub(r'.*(class|struct)\s*(\w+).*', r'\2',
                                    input_str.replace('\n', ' '))
                class_input = [class_name, p.classes[class_name]]
                obj_c = hpp2plantuml.hpp2plantuml.Class(class_input)
                nt.assert_equal(output_ref_str, obj_c.render(),
                                'Test {0} failed [input: {1}]'.format(test_idx,
                                                                      input_str))

Enum
^^^^

The unit test for enum objects includes rendering tests for the code segments in
Table `tbl-unittest-enum`_.

.. table:: List of test segments and corresponding PlantUML strings.
    :name: tbl-unittest-enum

    +-------------------------------------+-----------------------------------------+
    | C++                                 | plantuml                                |
    +=====================================+=========================================+
    | "enum Test { A, B, CD, E };"        | "enum Test {\n\tA\n\tB\n\tCD\n\tE\n}\n" |
    +-------------------------------------+-----------------------------------------+
    | "enum Test\n{\n A = 0, B = 12\n };" | "enum Test {\n\tA\n\tB\n}\n"            |
    +-------------------------------------+-----------------------------------------+
    | "enum { A, B };"                    | "enum empty {\n\tA\n\tB\n}\n""          |
    +-------------------------------------+-----------------------------------------+


.. code:: python
    :name: test-unit-enum

    # %% Test enum objects


    class TestEnum:
        def test_list_entries(self):
            for test_idx, (input_str, output_ref_str) in \
                enumerate(fix_test_list_def(test_list_enum)):
                p = get_parsed_element(input_str)
                enum_name = re.sub(r'.*enum\s*(\w+).*', r'\1',
                                   input_str.replace('\n', ' '))
                enum_input = p.enums[0]
                obj_c = hpp2plantuml.hpp2plantuml.Enum(enum_input)
                nt.assert_equal(output_ref_str, obj_c.render(),
                                'Test {0} failed [input: {1}]'.format(test_idx,
                                                                      input_str))

Links
^^^^^

The unit test for link objects includes rendering tests for the code segments in
Table `tbl-unittest-link`_.  It tests inheritance and aggregation
relationships (with and without count).


.. table:: List of test segments and corresponding PlantUML strings.
    :name: tbl-unittest-link

    +----------------------------------------------------------+----------------------------------+
    | C++                                                      | plantuml                         |
    +==========================================================+==================================+
    | "class A{};\nclass B : A{};"                             | "A <@-- B\n"                     |
    +----------------------------------------------------------+----------------------------------+
    | "class A{};\nclass B : public A{};"                      | "A <@-- B\n"                     |
    +----------------------------------------------------------+----------------------------------+
    | "class B{};\nclass A{B obj;};"                           | "A \*-- B\n"                     |
    +----------------------------------------------------------+----------------------------------+
    | "class B{};\nclass A{B\* obj;};"                         | "A o-- B\n"                      |
    +----------------------------------------------------------+----------------------------------+
    | "class B{};\nclass A{B \* obj\_ptr; B\* ptr;};"          | "A \\"2\\" o-- B\n"              |
    +----------------------------------------------------------+----------------------------------+
    | "class A{};\nclass B{void Method(A\* obj);};"            | "A <.. B\n"                      |
    +----------------------------------------------------------+----------------------------------+
    | "namespace T {class A{}; class B: A{};};"                | "namespace T {\n\tA <@-- B\n}\n" |
    +----------------------------------------------------------+----------------------------------+
    | "namespace T {\nclass A{};};\nclass B{T\:\:A\* \_obj;};" | ".B o-- T.A\n"                   |
    +----------------------------------------------------------+----------------------------------+


.. code:: python
    :name: test-unit-link

    class TestLink:
        def test_list_entries(self):
            for test_idx, (input_str, output_ref_str) in \
                enumerate(fix_test_list_def(test_list_link)):
                obj_d = hpp2plantuml.Diagram(flag_dep=True)
                # Not very unittest-y
                obj_d.create_from_string(input_str)
                if len(obj_d._inheritance_list) > 0:
                    obj_l = obj_d._inheritance_list[0]
                elif len(obj_d._aggregation_list) > 0:
                    obj_l = obj_d._aggregation_list[0]
                elif len(obj_d._dependency_list) > 0:
                    obj_l = obj_d._dependency_list[0]
                nt.assert_equal(output_ref_str, obj_l.render(),
                                'Test {0} failed [input: {1}]'.format(test_idx,
                                                                      input_str))

Full system test
~~~~~~~~~~~~~~~~

The system test uses example header files and validates the PlantUML string
rendering compared to a saved reference.

.. _sec-test-system-hpp:

Input files
^^^^^^^^^^^

The header is split into two files, in order to test the ability to load
multiple inputs.  It contains a mix of abstract, template classes with members
of different scope and with different properties (static, abstract methods,
etc.).

The following can be extended to improve testing, as long as the corresponding
`sec-test-system-ref`_ is kept up-to-date.

.. code:: c++
    :name: hpp-simple-classes-1-2

    enum Enum01 { VALUE_0, VALUE_1, VALUE_2 };

    class Class01 {
    protected:
    	int _protected_var;
    	bool _ProtectedMethod(int param);
    	static bool _StaticProtectedMethod(bool param);
    	virtual bool _AbstractMethod(int param) = 0;
    public:
    	Class01& operator=(const Class01&) & = delete;
    	int public_var;
    	bool PublicMethod(int param) const;
    	static bool StaticPublicMethod(bool param);
    	virtual bool AbstractPublicMethod(int param) = 0;
    };

    class Class02 : public Class01 {
    public:
    	bool AbstractPublicMethod(int param) override;
    private:
    	class ClassNested {
    		int var;
    	};
    	int _private_var;
    	template <typename T>
    	bool _PrivateMethod(T param);
    	static bool _StaticPrivateMethod(bool param);
    	bool _AbstractMethod(int param) override;
    };

.. code:: c++
    :name: hpp-simple-classes-3

    template<typename T>
    class Class03 {
    public:
    	Class03();
    	~Class03();
    	void Method(Interface::Class04& c4);
    private:
    	Class01* _obj;
    	Class01* _data;
    	list<Class02> _obj_list;
    	T* _typed_obj;
    };

    namespace Interface {

    	class Class04 {
    	public:
    		Class04();
    		~Class04();
    	private:
    		bool _flag;
    		Class01* _obj;
    		T _var;
    	};

    	class Class04_derived : public Class04 {
    	public:
    		Class04_derived();
    		~Class04_derived();
    	private:
    		int _var;
    	};

    	struct Struct {
    		int a;
    	};
    };

    // Anonymous union (issue #9)
    union {
    	struct {
    		float x;
    		float y;
    		float z;
    	};
    	struct {
    		float rho;
    		float theta;
    		float phi;
    	};
    	float vec[3];
    };

.. _sec-test-system-ref:

Reference output
^^^^^^^^^^^^^^^^

Following is the reference output for the input header files defined `sec-test-system-hpp`_.
The comparison takes into account the white space, indentation, etc.


::

    :name: puml-simple-classes

    @startuml





    /' Objects '/

    abstract class Class01 {
    	+{abstract} AbstractPublicMethod(int param) : bool
    	+PublicMethod(int param) : bool {query}
    	+{static} StaticPublicMethod(bool param) : bool
    	#{abstract} _AbstractMethod(int param) : bool
    	#_ProtectedMethod(int param) : bool
    	#{static} _StaticProtectedMethod(bool param) : bool
    	#_protected_var : int
    	+public_var : int
    }


    class Class02 {
    	+AbstractPublicMethod(int param) : bool
    	-_AbstractMethod(int param) : bool
    	-_PrivateMethod(T param) : bool
    	-{static} _StaticPrivateMethod(bool param) : bool
    	-_private_var : int
    }


    class Class02::ClassNested {
    	-var : int
    }


    class Class03 <template<typename T>> {
    	+Class03()
    	+~Class03()
    	-_data : Class01*
    	-_obj : Class01*
    	-_typed_obj : T*
    	-_obj_list : list<Class02>
    	+Method(Interface::Class04& c4) : void
    }


    namespace Interface {
    	class Class04 {
    		+Class04()
    		+~Class04()
    		-_obj : Class01*
    		-_var : T
    		-_flag : bool
    	}
    }


    namespace Interface {
    	class Class04_derived {
    		+Class04_derived()
    		+~Class04_derived()
    		-_var : int
    	}
    }


    enum Enum01 {
    	VALUE_0
    	VALUE_1
    	VALUE_2
    }


    namespace Interface {
    	class Struct {
    		+a : int
    	}
    }


    class anon-union-1::anon-struct-1 {
    	+x : float
    	+y : float
    	+z : float
    }


    class anon-union-1::anon-struct-2 {
    	+phi : float
    	+rho : float
    	+theta : float
    }


    class anon-union-1 {
    	+vec : float
    }





    /' Inheritance relationships '/

    .Class01 <|-- .Class02


    namespace Interface {
    	Class04 <|-- Class04_derived
    }





    /' Aggregation relationships '/

    .Class03 "2" o-- .Class01


    .Class03 *-- .Class02


    Interface.Class04 o-- .Class01






    /' Dependency relationships '/

    Interface.Class04 <.. .Class03





    @enduml

::

    :name: puml-simple-classes-no-dependency

    @startuml





    /' Objects '/

    abstract class Class01 {
    	+{abstract} AbstractPublicMethod(int param) : bool
    	+PublicMethod(int param) : bool {query}
    	+{static} StaticPublicMethod(bool param) : bool
    	#{abstract} _AbstractMethod(int param) : bool
    	#_ProtectedMethod(int param) : bool
    	#{static} _StaticProtectedMethod(bool param) : bool
    	#_protected_var : int
    	+public_var : int
    }


    class Class02 {
    	+AbstractPublicMethod(int param) : bool
    	-_AbstractMethod(int param) : bool
    	-_PrivateMethod(T param) : bool
    	-{static} _StaticPrivateMethod(bool param) : bool
    	-_private_var : int
    }


    class Class02::ClassNested {
    	-var : int
    }


    class Class03 <template<typename T>> {
    	+Class03()
    	+~Class03()
    	-_data : Class01*
    	-_obj : Class01*
    	-_typed_obj : T*
    	-_obj_list : list<Class02>
    	+Method(Interface::Class04& c4) : void
    }


    namespace Interface {
    	class Class04 {
    		+Class04()
    		+~Class04()
    		-_obj : Class01*
    		-_var : T
    		-_flag : bool
    	}
    }


    namespace Interface {
    	class Class04_derived {
    		+Class04_derived()
    		+~Class04_derived()
    		-_var : int
    	}
    }


    enum Enum01 {
    	VALUE_0
    	VALUE_1
    	VALUE_2
    }


    namespace Interface {
    	class Struct {
    		+a : int
    	}
    }


    class anon-union-1::anon-struct-1 {
    	+x : float
    	+y : float
    	+z : float
    }


    class anon-union-1::anon-struct-2 {
    	+phi : float
    	+rho : float
    	+theta : float
    }


    class anon-union-1 {
    	+vec : float
    }





    /' Inheritance relationships '/

    .Class01 <|-- .Class02


    namespace Interface {
    	Class04 <|-- Class04_derived
    }





    /' Aggregation relationships '/

    .Class03 "2" o-- .Class01


    .Class03 *-- .Class02


    Interface.Class04 o-- .Class01





    @enduml

Test diagram generation
^^^^^^^^^^^^^^^^^^^^^^^

The system test validates the following:

- input from multiple files, with and without wildcards,

- interfaces to the ``Diagram`` class listed in
  Table `tbl-diagram-interface`_,

- object reset,

- the ``CreatePlantUMLFile`` interface, including stdout and file output.  This
  test also includes a run with custom template.

::

    :name: test-full-template

    {% extends 'default.puml' %}

    {% block preamble %}
    title "This is a title"
    skinparam backgroundColor #EEEBDC
    skinparam handwritten true
    {% endblock %}


.. code:: python
    :name: test-full-diagram

    # %% Test overall system


    class TestFullDiagram():

        def __init__(self):
            self._input_files = ['simple_classes_1_2.hpp', 'simple_classes_3.hpp']
            self._input_files_w = ['simple_classes_*.hpp', 'simple_classes_3.hpp']
            self._diag_saved_ref = ''
            with open(os.path.join(test_fold, 'simple_classes.puml'), 'rt') as fid:
                self._diag_saved_ref = fid.read()
            self._diag_saved_ref_nodep = ''
            with open(os.path.join(test_fold,
                                   'simple_classes_nodep.puml'), 'rt') as fid:
                self._diag_saved_ref_nodep = fid.read()

        def test_full_files(self):
            self._test_full_files_helper(False)
            self._test_full_files_helper(True)

        def _test_full_files_helper(self, flag_dep=False):
            # Create first version
            file_list_ref = list(set(hpp2plantuml.hpp2plantuml.expand_file_list(
                [os.path.join(test_fold, f) for f in self._input_files])))
            diag_ref = hpp2plantuml.Diagram(flag_dep=flag_dep)
            diag_ref.create_from_file_list(file_list_ref)
            diag_render_ref = diag_ref.render()

            # Compare to saved reference
            if flag_dep:
                saved_ref = self._diag_saved_ref
            else:
                saved_ref = self._diag_saved_ref_nodep
            nt.assert_equal(saved_ref, diag_render_ref)

            # # Validate equivalent inputs

            # File expansion
            for file_list in [self._input_files, self._input_files_w]:
                file_list_c = list(set(hpp2plantuml.hpp2plantuml.expand_file_list(
                    [os.path.join(test_fold, f) for f in file_list])))

                # Create from file list
                diag_c = hpp2plantuml.Diagram(flag_dep=flag_dep)
                diag_c.create_from_file_list(file_list_c)
                nt.assert_equal(diag_render_ref, diag_c.render())

                # Add from file list
                diag_c_add = hpp2plantuml.Diagram(flag_dep=flag_dep)
                diag_c_add.add_from_file_list(file_list_c)
                diag_c_add.build_relationship_lists()
                diag_c_add.sort_elements()
                nt.assert_equal(diag_render_ref, diag_c_add.render())

                # Create from first file, add from rest of the list
                diag_c_file = hpp2plantuml.Diagram(flag_dep=flag_dep)
                diag_c_file.create_from_file(file_list_c[0])
                for file_c in file_list_c[1:]:
                    diag_c_file.add_from_file(file_c)
                diag_c_file.build_relationship_lists()
                diag_c_file.sort_elements()
                nt.assert_equal(diag_render_ref, diag_c_file.render())

            # String inputs
            input_str_list = []
            for file_c in file_list_ref:
                with open(file_c, 'rt') as fid:
                    input_str_list.append(fid.read())

            # Create from string list
            diag_str_list = hpp2plantuml.Diagram(flag_dep=flag_dep)
            diag_str_list.create_from_string_list(input_str_list)
            nt.assert_equal(diag_render_ref, diag_str_list.render())

            # Add from string list
            diag_str_list_add = hpp2plantuml.Diagram(flag_dep=flag_dep)
            diag_str_list_add.add_from_string_list(input_str_list)
            diag_str_list_add.build_relationship_lists()
            diag_str_list_add.sort_elements()
            nt.assert_equal(diag_render_ref, diag_str_list_add.render())

            # Create from string
            diag_str = hpp2plantuml.Diagram(flag_dep=flag_dep)
            diag_str.create_from_string('\n'.join(input_str_list))
            nt.assert_equal(diag_render_ref, diag_str.render())
            # Reset and parse
            diag_str.clear()
            diag_str.create_from_string('\n'.join(input_str_list))
            nt.assert_equal(diag_render_ref, diag_str.render())

            # Manually build object
            diag_manual_add = hpp2plantuml.Diagram(flag_dep=flag_dep)
            for idx, (file_c, string_c) in enumerate(zip(file_list_ref,
                                                         input_str_list)):
                if idx == 0:
                    diag_manual_add.add_from_file(file_c)
                else:
                    diag_manual_add.add_from_string(string_c)
            diag_manual_add.build_relationship_lists()
            diag_manual_add.sort_elements()
            nt.assert_equal(diag_render_ref, diag_manual_add.render())

        def test_main_function(self):
            #self._test_main_function_helper(False)
            self._test_main_function_helper(True)

        def _test_main_function_helper(self, flag_dep=False):

            # List files
            file_list = [os.path.join(test_fold, f) for f in self._input_files]

            # Output to string
            with io.StringIO() as io_stream:
                sys.stdout = io_stream
                hpp2plantuml.CreatePlantUMLFile(file_list, flag_dep=flag_dep)
                io_stream.seek(0)
                # Read string output, exclude final line return
                output_str = io_stream.read()[:-1]
            sys.stdout = sys.__stdout__
            if flag_dep:
                saved_ref = self._diag_saved_ref
            else:
                saved_ref = self._diag_saved_ref_nodep
            nt.assert_equal(saved_ref, output_str)

            # Output to file
            output_fname = 'output.puml'
            for template in [None, os.path.join(test_fold,
                                                'custom_template.puml')]:
                hpp2plantuml.CreatePlantUMLFile(file_list, output_fname,
                                                template_file=template,
                                                flag_dep=flag_dep)
                output_fcontent = ''
                with open(output_fname, 'rt') as fid:
                    output_fcontent = fid.read()
                if template is None:
                    # Default template check
                    nt.assert_equal(saved_ref, output_fcontent)
                else:
                    # Check that all lines of reference are in the output
                    ref_re = re.search('(@startuml)\s*(.*)', saved_ref, re.DOTALL)
                    assert ref_re
                    # Build regular expression: allow arbitrary text between
                    # @startuml and the rest of the string
                    ref_groups = ref_re.groups()
                    match_re = re.compile('\n'.join([
                        re.escape(ref_groups[0]),    # @startuml line
                        '.*',                        # preamble
                        re.escape(ref_groups[1])]),  # main output
                                          re.DOTALL)
                    nt.assert_true(match_re.search(output_fcontent))
            os.unlink(output_fname)

Packaging
---------

In order to distribute and publish the hpp2plantuml module to `PyPI <https://pypi.python.org/pypi>`_, the
``setuptools`` package was used.

The following guides summarize the packaging process and provide useful
examples:

- `https://hynek.me/articles/sharing-your-labor-of-love-pypi-quick-and-dirty/ <https://hynek.me/articles/sharing-your-labor-of-love-pypi-quick-and-dirty/>`_

- `https://python-packaging.readthedocs.io/en/latest/ <https://python-packaging.readthedocs.io/en/latest/>`_

- `https://packaging.python.org/distributing/ <https://packaging.python.org/distributing/>`_

To build, run ``python setup.py build bdist``, ``python setup.py build bdist_wheel``.  To upload to PyPI, run:

::

    twine upload -r pypi --sign dist/hpp2plantuml-*

``__init__.py``
~~~~~~~~~~~~~~~

The module's init file simply defines meta variables required by ``setuptools``.
It also imports the main interface: the ``CreatePlantUMLFile`` function and the
``Diagram`` class for use as a module.

The header is filled with the content of org-mode blocks.  The version number is
obtained using the source block described `sec-org-el-version`_.

.. code:: python
    :name: py-init

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
    __version__ = '0.7.1'
    __uri__ = "https://github.com/thibaultmarin/hpp2plantuml"
    __doc__ = __description__ + " <" + __uri__ + ">"
    __author__ = "Thibault Marin"
    __email__ = "thibault.marin@gmx.com"
    __license__ = "MIT"
    __copyright__ = "Copyright (c) 2016 Thibault Marin"

    from .hpp2plantuml import CreatePlantUMLFile, Diagram

    __all__ = ['CreatePlantUMLFile', 'Diagram']

``setup.cfg``
~~~~~~~~~~~~~

The ``setup.cfg`` file defines some basic properties of the package.  It forces
"universal" wheel builds, sets the license file and defines documentation
commands.

The `sec-package-doc`_ uses `Sphinx <http://sphinx-doc.org>`_ to generate the HTML documentation.  The
``build_sphinx`` configuration defines the location for the input and output
documentation files.  In practice, the documentation is built using a `sec-package-doc`_ for ``setup.py`` run using ``python setup.py sphinx``.

::

    :name: cfg-setup


    [bdist_wheel]
    universal = 1

    [metadata]
    license_file = LICENSE

    [build_sphinx]
    source-dir = doc/source
    build-dir  = doc/build
    all_files  = 1

    [upload_sphinx]
    upload-dir = doc/build/html

.. _sec-package-setup-py:

``setup.py``
~~~~~~~~~~~~

The ``setup.py`` file is the interface to ``setuptools``.  It defines the packaging
options.  Most of it is taken from `this post <https://hynek.me/articles/sharing-your-labor-of-love-pypi-quick-and-dirty/>`_.

.. code:: python
    :name: py-setup-import


    # %% Imports
    import os
    import sys
    import re
    import codecs

    from setuptools import setup, find_packages, Command
    try:
        import sphinx
        import sphinx.ext.apidoc
        import sphinx.cmd.build
    except ImportError:
        pass

Custom content
^^^^^^^^^^^^^^

The non-boilerplate part of the ``setup.py`` file defines the package information.

.. code:: python
    :name: py-setup-custom

    # %% Custom fields

    ###################################################################

    NAME = "hpp2plantuml"
    PACKAGES = find_packages(where="src")
    META_PATH = os.path.join("src", NAME, "__init__.py")
    KEYWORDS = ["class"]
    CLASSIFIERS = [
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ]
    INSTALL_REQUIRES = ['argparse', 'robotpy-cppheaderparser', 'jinja2']
    INSTALL_REQUIRES += ['sphinx', ]
    SETUP_REQUIRES = ['sphinx', 'numpydoc']
    ###################################################################

Helper functions
^^^^^^^^^^^^^^^^

The following helper functions provide tools to extract metadata from the
``__init__`` file and pass it to the ``setup`` command.

.. code:: python
    :name: py-setup-helper


    HERE = os.path.abspath(os.path.dirname(__file__))


    def read(*parts):
        """
        Build an absolute path from *parts* and and return the contents of the
        resulting file.  Assume UTF-8 encoding.
        """
        with codecs.open(os.path.join(HERE, *parts), "rb", "utf-8") as f:
            return f.read()


    META_FILE = read(META_PATH)


    def find_meta(meta):
        """
        Extract __*meta*__ from META_FILE.
        """
        meta_match = re.search(
            r"^__{meta}__ = ['\"]([^'\"]*)['\"]".format(meta=meta),
            META_FILE, re.M
        )
        if meta_match:
            return meta_match.group(1)
        raise RuntimeError("Unable to find __{meta}__ string.".format(meta=meta))

    # %% Sphinx Build


    class Sphinx(Command):
        user_options = []
        description = 'Build sphinx documentation'

        def initialize_options(self):
            pass

        def finalize_options(self):
            pass

        def run(self):
            metadata = self.distribution.metadata
            src_dir = (self.distribution.package_dir or {'': ''})['']
            src_dir = os.path.join(os.getcwd(),  src_dir)
            sys.path.append('src')
            # Run sphinx by calling the main method, '--full' also adds a
            # conf.py
            sphinx.ext.apidoc.main(
                ['--private', '-H', metadata.name,
                 '-A', metadata.author,
                 '-V', metadata.version,
                 '-R', metadata.version,
                 '-o', os.path.join('doc', 'source'), src_dir]
            )
            # build the doc sources
            sphinx.cmd.build.main([os.path.join('doc', 'source'),
                                   os.path.join('doc', 'build', 'html')])

Setup
^^^^^

This final block passes all the relevant package information to ``setuptools``:

- package information: name, author, license, requirements,

- source code location,

- testing framework,

- console script: the package installs the ``hpp2plantuml`` `sec-module-cmd`_.

.. code:: python
    :name: py-setup-main


    if __name__ == "__main__":
        setup(
            name=NAME,
            description=find_meta("description"),
            license=find_meta("license"),
            url=find_meta("uri"),
            version=find_meta("version"),
            author=find_meta("author"),
            author_email=find_meta("email"),
            maintainer=find_meta("author"),
            maintainer_email=find_meta("email"),
            keywords=KEYWORDS,
            long_description=read("README.rst"),
            packages=PACKAGES,
            package_dir={"": "src"},
            package_data={PACKAGES[0]: ['templates/*.puml']},
            include_package_data=True,
            zip_safe=False,
            classifiers=CLASSIFIERS,
            install_requires=INSTALL_REQUIRES,
            setup_requires=SETUP_REQUIRES,
            test_suite='nose.collector',
            tests_require=['nose'],
            entry_points={
                'console_scripts': ['hpp2plantuml=hpp2plantuml.hpp2plantuml:main']
            },
            cmdclass={'sphinx': Sphinx}(ref:setup-sphinx)
        )

Manifest
~~~~~~~~

The manifest file is used to include extra files to the package.

::

    :name: setup-manifest

    include *.rst *.txt LICENSE
    recursive-include tests *.py
    recursive-include tests *.hpp
    recursive-include tests *.puml
    recursive-include doc *.rst
    recursive-include doc *.py
    prune doc/build

README
~~~~~~

The README file is automatically generated from blocks defined in this
org-file (converted to RST format).

.. code:: rst
    :name: rst-README


    hpp2plantuml - Convert C++ header files to PlantUML
    ===================================================

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

    - dependency relationships

    The package relies on the `CppHeaderParser <https://pypi.org/project/robotpy-cppheaderparser/>`_ package for parsing of C++ header
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


    .. _sec-module-install:

    Installation
    ------------

    Using ``pip``
    ~~~~~~~~~~~~~

    The package is available on `PyPi <https://pypi.python.org/>`_ and can be installed using pip:

    ::

        pip install hpp2plantuml

    From source
    ~~~~~~~~~~~

    The code uses ``setuptools``, so it can be built using:

    ::

        python setup.py install

    To build the documentation, run:

    ::

        python setup.py sphinx

    To run the tests, run:

    ::

        python setup.py test


    The full documentation is available via:

    - `This org-mode post <https://thibaultmarin.github.io/blog/posts/2016-11-30-hpp2plantuml_-_Convert_C++_header_files_to_PlantUML.html>`_
    - `Read the docs <http://hpp2plantuml.readthedocs.io/en/latest/>`_

.. _sec-package-doc:

Documentation
~~~~~~~~~~~~~

The module documentation is this org-file, which contains everything from the
module code to tests, packaging and documentation.

In order to distribute the package on standard platforms, a RST documentation is
also generated using `Sphinx <http://sphinx-doc.org>`_.  The ``setup.py`` file contains a custom command
"sphinx" to build the documentation.

The documentation is composed of two parts:

- this org-file is fully exported to RST,

- the ``sphinx-api`` program is used to generate the module documentation from
  docstrings in the code.

Sphinx configuration
^^^^^^^^^^^^^^^^^^^^

Sphinx configuration is performed via the ``conf.py`` file.  An example
configuration file can be generated using the ``sphinx-quickstart`` command.  The
content of the file is mostly following the defaults, with a few exceptions:

- the system path is modified to include the path to the package source code
  (22),

- the ``numpydoc`` package is used to render the docstrings
  (53).

.. code:: python
    :name: py-sphinx-conf


    # -*- coding: utf-8 -*-
    #
    # hpp2plantuml documentation build configuration file, created by
    # sphinx-quickstart on Fri Dec  9 13:26:02 2016.
    #
    # This file is execfile()d with the current directory set to its
    # containing dir.
    #
    # Note that not all possible configuration values are present in this
    # autogenerated file.
    #
    # All configuration values have a default; values that are commented out
    # serve to show the default.

    # If extensions (or modules to document with autodoc) are in another directory,
    # add these directories to sys.path here. If the directory is relative to the
    # documentation root, use os.path.abspath to make it absolute, like shown here.
    #
    import os
    import sys
    # sys.path.insert(0, os.path.abspath('.'))
    sys.path.insert(0, os.path.abspath("../.."))(ref:sphinx-conf-path)

    # Customizations

    autoclass_content = 'both'
    autodoc_default_flags = ['members', 'undoc-members', 'private-members']
    numpydoc_show_class_members = False

    # Customizations

    autoclass_content = 'both'
    autodoc_default_flags = ['members', 'undoc-members', 'private-members']

    # -- General configuration ------------------------------------------------

    # If your documentation needs a minimal Sphinx version, state it here.
    #
    # needs_sphinx = '1.0'

    # Add any Sphinx extension module names here, as strings. They can be
    # extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
    # ones.
    extensions = [
        'sphinx.ext.autodoc',
        'sphinx.ext.intersphinx',
        'sphinx.ext.todo',
        'sphinx.ext.coverage',
        'sphinx.ext.mathjax',
        'sphinx.ext.ifconfig',
        'sphinx.ext.viewcode',
        'sphinx.ext.autosummary',
        'numpydoc'(ref:sphinx-conf-numpydoc)
    ]

    # Add any paths that contain templates here, relative to this directory.
    templates_path = ['_templates']

    # The suffix(es) of source filenames.
    # You can specify multiple suffix as a list of string:
    #
    # source_suffix = ['.rst', '.md']
    source_suffix = '.rst'

    # The encoding of source files.
    #
    # source_encoding = 'utf-8-sig'

    # The master toctree document.
    master_doc = 'index'

    # General information about the project.
    project = u'hpp2plantuml'
    copyright = u'2016, Thibault Marin'
    author = u'Thibault Marin'

    # The version info for the project you're documenting, acts as replacement for
    # |version| and |release|, also used in various other places throughout the
    # built documents.
    #
    # The short X.Y version.
    version = u'v' + u'0.7.1'
    # The full version, including alpha/beta/rc tags.
    release = u'v' + u'0.7.1'

    # The language for content autogenerated by Sphinx. Refer to documentation
    # for a list of supported languages.
    #
    # This is also used if you do content translation via gettext catalogs.
    # Usually you set "language" from the command line for these cases.
    language = 'en'

    # There are two options for replacing |today|: either, you set today to some
    # non-false value, then it is used:
    #
    # today = ''
    #
    # Else, today_fmt is used as the format for a strftime call.
    #
    # today_fmt = '%B %d, %Y'

    # List of patterns, relative to source directory, that match files and
    # directories to ignore when looking for source files.
    # This patterns also effect to html_static_path and html_extra_path
    exclude_patterns = []

    # The reST default role (used for this markup: `text`) to use for all
    # documents.
    #
    default_role = 'autolink'

    # If true, '()' will be appended to :func: etc. cross-reference text.
    #
    # add_function_parentheses = True

    # If true, the current module name will be prepended to all description
    # unit titles (such as .. function::).
    #
    # add_module_names = True

    # If true, sectionauthor and moduleauthor directives will be shown in the
    # output. They are ignored by default.
    #
    # show_authors = False

    # The name of the Pygments (syntax highlighting) style to use.
    pygments_style = 'sphinx'

    # A list of ignored prefixes for module index sorting.
    # modindex_common_prefix = []

    # If true, keep warnings as "system message" paragraphs in the built documents.
    # keep_warnings = False

    # If true, `todo` and `todoList` produce output, else they produce nothing.
    todo_include_todos = True


    # -- Options for HTML output ----------------------------------------------

    # The theme to use for HTML and HTML Help pages.  See the documentation for
    # a list of builtin themes.
    #
    html_theme = 'alabaster'

    # Theme options are theme-specific and customize the look and feel of a theme
    # further.  For a list of options available for each theme, see the
    # documentation.
    #
    # html_theme_options = {}

    # Add any paths that contain custom themes here, relative to this directory.
    # html_theme_path = []

    # The name for this set of Sphinx documents.
    # "<project> v<release> documentation" by default.
    #
    # html_title = u'hpp2plantuml ' + u'v' + u'0.7.1'

    # A shorter title for the navigation bar.  Default is the same as html_title.
    #
    # html_short_title = None

    # The name of an image file (relative to this directory) to place at the top
    # of the sidebar.
    #
    # html_logo = None

    # The name of an image file (relative to this directory) to use as a favicon of
    # the docs.  This file should be a Windows icon file (.ico) being 16x16 or 32x32
    # pixels large.
    #
    # html_favicon = None

    # Add any paths that contain custom static files (such as style sheets) here,
    # relative to this directory. They are copied after the builtin static files,
    # so a file named "default.css" will overwrite the builtin "default.css".
    html_static_path = ['_static']

    # Add any extra paths that contain custom files (such as robots.txt or
    # .htaccess) here, relative to this directory. These files are copied
    # directly to the root of the documentation.
    #
    # html_extra_path = []

    # If not None, a 'Last updated on:' timestamp is inserted at every page
    # bottom, using the given strftime format.
    # The empty string is equivalent to '%b %d, %Y'.
    #
    # html_last_updated_fmt = None

    # If true, SmartyPants will be used to convert quotes and dashes to
    # typographically correct entities.
    #
    # html_use_smartypants = True

    # Custom sidebar templates, maps document names to template names.
    #
    # html_sidebars = {}

    # Additional templates that should be rendered to pages, maps page names to
    # template names.
    #
    # html_additional_pages = {}

    # If false, no module index is generated.
    #
    # html_domain_indices = True

    # If false, no index is generated.
    #
    # html_use_index = True

    # If true, the index is split into individual pages for each letter.
    #
    # html_split_index = False

    # If true, links to the reST sources are added to the pages.
    #
    # html_show_sourcelink = True

    # If true, "Created using Sphinx" is shown in the HTML footer. Default is True.
    #
    # html_show_sphinx = True

    # If true, "(C) Copyright ..." is shown in the HTML footer. Default is True.
    #
    # html_show_copyright = True

    # If true, an OpenSearch description file will be output, and all pages will
    # contain a <link> tag referring to it.  The value of this option must be the
    # base URL from which the finished HTML is served.
    #
    # html_use_opensearch = ''

    # This is the file name suffix for HTML files (e.g. ".xhtml").
    # html_file_suffix = None

    # Language to be used for generating the HTML full-text search index.
    # Sphinx supports the following languages:
    #   'da', 'de', 'en', 'es', 'fi', 'fr', 'hu', 'it', 'ja'
    #   'nl', 'no', 'pt', 'ro', 'ru', 'sv', 'tr', 'zh'
    #
    # html_search_language = 'en'

    # A dictionary with options for the search language support, empty by default.
    # 'ja' uses this config value.
    # 'zh' user can custom change `jieba` dictionary path.
    #
    # html_search_options = {'type': 'default'}

    # The name of a javascript file (relative to the configuration directory) that
    # implements a search results scorer. If empty, the default will be used.
    #
    # html_search_scorer = 'scorer.js'

    # Output file base name for HTML help builder.
    htmlhelp_basename = 'hpp2plantumldoc'

    # -- Options for LaTeX output ---------------------------------------------

    latex_elements = {
         # The paper size ('letterpaper' or 'a4paper').
         #
         # 'papersize': 'letterpaper',

         # The font size ('10pt', '11pt' or '12pt').
         #
         # 'pointsize': '10pt',

         # Additional stuff for the LaTeX preamble.
         #
         # 'preamble': '',

         # Latex figure (float) alignment
         #
         # 'figure_align': 'htbp',
    }

    # Grouping the document tree into LaTeX files. List of tuples
    # (source start file, target name, title,
    #  author, documentclass [howto, manual, or own class]).
    latex_documents = [
        (master_doc, 'hpp2plantuml.tex', u'hpp2plantuml Documentation',
         u'Thibault Marin', 'manual'),
    ]

    # The name of an image file (relative to this directory) to place at the top of
    # the title page.
    #
    # latex_logo = None

    # For "manual" documents, if this is true, then toplevel headings are parts,
    # not chapters.
    #
    # latex_use_parts = False

    # If true, show page references after internal links.
    #
    # latex_show_pagerefs = False

    # If true, show URL addresses after external links.
    #
    # latex_show_urls = False

    # Documents to append as an appendix to all manuals.
    #
    # latex_appendices = []

    # It false, will not define \strong, \code, 	itleref, \crossref ... but only
    # \sphinxstrong, ..., \sphinxtitleref, ... To help avoid clash with user added
    # packages.
    #
    # latex_keep_old_macro_names = True

    # If false, no module index is generated.
    #
    # latex_domain_indices = True


    # -- Options for manual page output ---------------------------------------

    # One entry per manual page. List of tuples
    # (source start file, name, description, authors, manual section).
    man_pages = [
        (master_doc, 'hpp2plantuml', u'hpp2plantuml Documentation',
         [author], 1)
    ]

    # If true, show URL addresses after external links.
    #
    # man_show_urls = False


    # -- Options for Texinfo output -------------------------------------------

    # Grouping the document tree into Texinfo files. List of tuples
    # (source start file, target name, title, author,
    #  dir menu entry, description, category)
    texinfo_documents = [
        (master_doc, 'hpp2plantuml', u'hpp2plantuml Documentation',
         author, 'hpp2plantuml', 'One line description of project.',
         'Miscellaneous'),
    ]

    # Documents to append as an appendix to all manuals.
    #
    # texinfo_appendices = []

    # If false, no module index is generated.
    #
    # texinfo_domain_indices = True

    # How to display URL addresses: 'footnote', 'no', or 'inline'.
    #
    # texinfo_show_urls = 'footnote'

    # If true, do not generate a @detailmenu in the "Top" node's menu.
    #
    # texinfo_no_detailmenu = False


    # Example configuration for intersphinx: refer to the Python standard library.
    intersphinx_mapping = {'https://docs.python.org/': None}

Index page
^^^^^^^^^^

The index page is the entry point of the documentation.  It is formed by other
parts of the org document including a brief description of the usage and links
to the automatically generated and the org-file documents.

.. code:: rst
    :name: doc-rst-index


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

    - dependency relationships

    The package relies on the `CppHeaderParser <https://pypi.org/project/robotpy-cppheaderparser/>`_ package for parsing of C++ header
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

Read The Docs
^^^^^^^^^^^^^

In order to build the documentation on the `Read The Docs <http://read-the-docs.readthedocs.io/en/latest/>`_ website, a requirement
file is added for the ``numpydoc`` package.

::

    :name: req-readthedocs

    numpydoc

Org-mode setup
--------------

The generation of the package code depends on org-mode, mostly to expand blocks
with the ```noweb`` <http://orgmode.org/manual/Noweb-reference-syntax.html>`_ interface.  The following defines helper functions to simplify
this process.

.. _sec-org-el-version:

Version string
~~~~~~~~~~~~~~

The following source block is used to get the module's version number defined in
`a single location <hpp2plantuml-version>`_ and include it at multiple locations.

.. code:: common-lisp
    :name: get-version

    (cond ((string= lang "python")
           (format "'%s'" ver)))

org-to-rst
~~~~~~~~~~

The following source block converts the content of an org heading to rst format
using the ``org-rst-convert-region-to-rst`` function.  The heading to process is
passed by its CUSTOM\_ID property (as a string).  In addition, the output
language can be set (although rst is the only instance used in this document)
and an additional flag ``children`` can be used to control whether the subsections
of the target section are removed (``children = "remove"``) of kept (any other
string, e.g. ``"keep"``).

.. code:: common-lisp
    :name: el-org-exp

    (save-excursion
      (let ((org-tree (org-element-parse-buffer)))
        (org-element-map
            org-tree 'headline
          (lambda (r)
            (let ((cid (org-element-property :CUSTOM_ID r)))
              ;; Find desired heading (identified by CUSTOM_ID)
              (when (string= cid input)
                (when (string= children "remove")
                  ;; Remove all children
                  (org-element-map (org-element-contents r) 'headline
                    (lambda (subr)
                      (org-element-extract-element subr))))
                (let ((out-text (org-element-interpret-data r)))
                      ;; Convert to output format
                      (cond ((string= lang "rst")
                             (with-temp-buffer
                               (insert out-text)
                               (mark-whole-buffer)
                               (let ((org-export-with-toc nil)
                                     (org-export-with-todo-keywords nil)
                                     (org-export-with-section-numbers nil)
                                     (org-export-with-broken-links t))
                                 (org-rst-convert-region-to-rst))(ref:rst-convert-region)
                               (buffer-string)))
                            ;; Could support more languages
                            (t out-text))))))
          nil t)))

Generate documentation
~~~~~~~~~~~~~~~~~~~~~~

When generating the rst documentation from this org-file, special handling is
required for source languages known to org but not to rst..  This is performed
using org's `filtering functionality <http://orgmode.org/manual/Advanced-configuration.html>`_.  The ``custom-rst-filter-org-block`` function
defines the filter responsible for post-processing source blocks when exporting
to rst.  Its goal is to fix languages unknown to sphinx (which relies on `the
pygmentize program <http://pygments.org/>`_ for syntax highlighting) such as ``plantuml`` and org's ``conf``
blocks, replacing them by a simple example block.

.. code:: common-lisp
    :name: ox-rst-filter-src

    (defun custom-rst-filter-org-block (text backend info)(ref:el-rst-filter)
      (when (org-export-derived-backend-p backend 'rst)
        (let* ((pattern ".*\.\. code:: \\([[:alnum:]]+\\)")
               (pattern-line (concat pattern ".*$"))
               (lang (progn
                       (string-match pattern text)
                       (match-string 1 text))))
          (cond ((member lang '("conf" "plantuml"))
                 (replace-regexp-in-string pattern-line "::\n" text))
                (t text)))))

The command and options to generate the org-file documentation in rst format are
encapsulated in the following source block.

.. code:: common-lisp
    :name: el-export-rst-org-doc

    (require 'ox-rst)
    (let ((org-export-with-toc nil)
          (org-export-with-todo-keywords nil)
          (org-export-with-section-numbers nil)
          (org-export-with-broken-links t)
          (org-export-filter-src-block-functions
           '(custom-rst-filter-org-block)))
      (org-export-to-file 'rst "doc/source/org-doc.rst"))
