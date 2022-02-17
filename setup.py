""" setup script """
import setuptools

exec(open("gfdlvitals/version.py").read())

setuptools.setup(version=__version__)
