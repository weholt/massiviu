#!/usr/bin/env python

try:
    from setuptools import setup
except (ImportError):
    from distribute import setup

setup(name='massiviu',
      version='1.0.0 Beta 2',
      description='MassivIU - Simplified "bulk" insert/update/delete for Django.',
      author='Thomas Weholt',
      author_email='thomas@weholt.org',
      long_description=open('README.md').read(),
      include_package_data=True,
      packages=['massiviu', ],
      test_suite = 'massiviu.testsuite',
      url="https://github.com/weholt/massiviu",
      requires=['django'],
      classifiers=[
          'Development Status :: 4 - Beta',
          'Intended Audience :: Developers',
          'Framework :: Django',
          'License :: OSI Approved :: BSD License',
          'Operating System :: OS Independent',
          'Programming Language :: Python',
          'Topic :: Database',
      ],
)
