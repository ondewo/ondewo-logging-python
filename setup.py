import setuptools

with open("README.md", "r") as f:
    long_description = f.read()

with open("requirements.txt") as f:
    requires = f.read().splitlines()

setuptools.setup(
    name="ondewo-logging",
    version="1.6.1",
    author="Ondewo GbmH",
    author_email="info@ondewo.com",
    description="This library provides custom logging for python including error handling and timing.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://bitbucket.org/ondewo/ondewo-logging",
    packages=[
        np
        for np in filter(
            lambda n: n.startswith('ondewo.') or n == 'ondewo',
            setuptools.find_packages()
        )
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
        "Topic :: Software Development :: Libraries",
    ],
    python_requires=">2.6, !=3.0.*, !=3.1.*",
    include_package_data=True,
    install_requires=requires,
)
