from setuptools import setup


setup(
    name='Typo',
    version='0.0.1',
    url='http://github.com/smarttelemax/typo/',
    license='MIT',
    author='John Smith',
    author_email='contact@smarttelemax.ru',
    description='Spelling errors correction for the search engine '
                ' (based on SphinxSearch) on your site.',
    packages=['typo', 'typo.correctors'],
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    install_requires=[
        'trollius==2.0',
        'python-Levenshtein==0.12.0',
        'click>=2.0',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    entry_points='''
        [console_scripts]
        typo=typo.cli:main
    '''
)
