import setuptools

setuptools.setup(
    name="gfdlvitals",
    version="3.0a1",
    author="John Krasting",
    author_email="John.Krasting@noaa.gov",
    description="A package for computing global means from GFDL models",
    #long_description=long_description,
    #long_description_content_type="text/markdown",
    url="https://gitlab.gfdl.noaa.gov/john.krasting/vitals",
    scripts=['scripts/gfdlvitals','scripts/db2nc'],
    packages=setuptools.find_packages(),
)
