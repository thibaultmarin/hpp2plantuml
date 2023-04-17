# %% Imports
import os
import sys
import re
import codecs

from setuptools import setup, find_namespace_packages, Command
try:
    import sphinx
    import sphinx.ext.apidoc
    import sphinx.cmd.build
except ImportError:
    pass

# %% Custom fields

###################################################################

NAME = "hpp2plantuml"
PACKAGES = find_namespace_packages(where="src")
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
    "Programming Language :: Python :: Implementation :: PyPy",
    "Topic :: Software Development :: Libraries :: Python Modules",
]
INSTALL_REQUIRES = ['argparse', 'robotpy-cppheaderparser', 'jinja2']
INSTALL_REQUIRES += ['sphinx', ]
SETUP_REQUIRES = ['sphinx', 'numpydoc']
###################################################################

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
        test_suite='pytest',
        tests_require=['pytest'],
        entry_points={
            'console_scripts': ['hpp2plantuml=hpp2plantuml.hpp2plantuml:main']
        },
        cmdclass={'sphinx': Sphinx}
    )
