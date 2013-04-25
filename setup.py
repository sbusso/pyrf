#!/usr/bin/env python

try:
    import setuptools
    def setup(**kwargs):
        setuptools.setup(zip_safe=False, **kwargs)
except ImportError:
    from distutils.core import setup

setup(
    name='pyrf',
    version='0.2.6',
    author='ThinkRF Corporation',
    author_email='support@thinkrf.com',
    packages=['pyrf', 'pyrf.devices'],
    url='https://github.com/pyrf/pyrf',
    license='BSD',
    description='API for RF receivers including ThinkRF WSA4000',
    long_description=open('README.rst').read(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: MacOS X",
        "Environment :: Win32 (MS Windows)",
        "Environment :: X11 Applications :: Qt",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: BSD License",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.5",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Topic :: Scientific/Engineering",
        "Topic :: Scientific/Engineering :: Visualization",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Software Development :: Testing",
        "Topic :: System :: Hardware",
        ],
)
