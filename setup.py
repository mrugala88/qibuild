from distutils.core import setup
import sys
import os


packages = [
    "qitools",
    "qitools.external",
    "qisrc",
    "qisrc.actions",
    "qibuild",
    "qibuild.actions",
    "qitoolchain",
    "qitoolchain.actions",
]

scripts = [
    "../bin/qisrc",
    "../bin/qibuild",
    "../bin/qitoolchain",
]

package_data = {
 "qibuild" : ["templates/build.cfg"]
}


setup(name = 'qibuild',
      version = "0.1",
      description = "The QiBuild Framework",
      author = "Aldebaran Robotics",
      author_email = "qi-dev@aldebaran-robotics.com",
      packages = packages,
      package_data = package_data,
      license = "BSD",
      scripts = scripts
)
