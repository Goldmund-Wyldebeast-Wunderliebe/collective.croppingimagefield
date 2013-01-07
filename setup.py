from setuptools import setup, find_packages
import os

version = '0.1'

setup(name='collective.croppingimagefield',
      version=version,
      description="Provides an image field that can crop, zoom or scale an image instead of just scaling it",
      long_description=open("collective/croppingimagefield/README.txt").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      # Get more strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Framework :: Plone",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2.4",
        "Topic :: Multimedia :: Graphics :: Graphics Conversion",
        "Topic :: Software Development",
        ],
      keywords='',
      author='Jonathan Riboux',
      author_email='jonathan.riboux@gmail.com',
      url='http://svn.plone.org/svn/collective/collective.croppingimagefield',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['collective'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      # -*- Entry points: -*-

      [distutils.setup_keywords]
      paster_plugins = setuptools.dist:assert_string_list

      [egg_info.writers]
      paster_plugins.txt = setuptools.command.egg_info:write_arg
      """,
      paster_plugins = ["ZopeSkel"],
      )
