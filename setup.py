import setuptools

with open('README.rst') as fp:
    long_description = fp.read()

setuptools.setup(
    name='gather',
    license='MIT',
    description="Gather: A gatherer.",
    long_description=long_description,
    use_incremental=True,
    setup_requires=['incremental'],
    author="Moshe Zadka",
    author_email="zadka.moshe@gmail.com",
    packages=setuptools.find_packages(where='src'),
    project_urls={
        'Development': 'https://github.com/elcaminoreal/gather',
        'Documentation': 'https://gather.readthedocs.io/en/latest/',
        'Blog': 'https://gather.works',
    },
    package_dir={"": "src"},
    install_requires=['attrs', 'incremental', 'venusian', 'six'],
    entry_points={
        'gather': [
             "gather=gather:gather",
        ]
    }
)
