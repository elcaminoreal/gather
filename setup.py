import setuptools

setuptools.setup(
    name='gather',
    license='MIT',
    description="Gather: A gatherer.",
    long_description="Such gather. Much gathering.",
    use_incremental=True,
    setup_requires=['incremental'],
    author="Moshe Zadka",
    author_email="zadka.moshe@gmail.com",
    packages=setuptools.find_packages(where='src'),
    package_dir={"": "src"},
    install_requires=['incremental', 'venusian', 'six'],
    entry_points={
        'gather': [
             "gather=gather:gather",
        ]
    }
)
