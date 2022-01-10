import setuptools

with open("readme.md", "r") as fh:
    long_description = fh.read()

with open("requirements.txt") as f:
    install_requires = f.read().splitlines()

setuptools.setup(
    name="bendev",
    version="0.0.1",
    author="Markus Führer",
    description="Control module for Bentham Instruments Ltd SCPI devices",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    license_files = ('LICENSE',),
    license = "MIT",
    url = "https://github.com/BenthamInstruments/bendev",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3 :: Only",
        "License :: OSI Approved :: MIT License",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX",
        "Topic :: System :: Hardware :: Hardware Drivers"
        "Topic :: System :: Hardware :: Universal Serial Bus (USB) :: Human Interface Device (HID)",
        "Intended Audience :: Science/Research",
    ],
    python_requires='>=3.8',
    py_modules=["bendev"],
    install_requires=install_requires
)