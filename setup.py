import setuptools

setuptools.setup(
    name='caparg',
    license='MIT',
    description="Captain Arguments.",
    long_description="Such Captain. So Argument.",
    use_incremental=True,
    setup_requires=['incremental'],
    author="Moshe Zadka",
    author_email="zadka.moshe@gmail.com",
    packages=setuptools.find_packages(where='src'),
    package_dir={"": "src"},
    install_requires=['incremental', 'venusian', 'six'],
    entry_points={
        'caparg': [
             "caparg=caparg:caparg",
        ]
    }
)
