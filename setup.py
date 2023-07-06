from setuptools import setup, find_packages

setup(
    name='zunda',
    version='0.1',
    author='Masaki Saito',
    author_email='msaito@preferred.jp',
    description='A simple python package for creating zunda-mon videos',
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'zunda': ['assets/*'],
    },
    python_requires=">3.9.0",
    install_requires=[
        'pandas>=1.0.1',
        'numpy>=1.18.1',
        'pydub>=0.25.1',
        'Pillow>=8.2.0',
        'pdf2image>=1.16.3',
        'mecab-python3>=1.0.3',
        'ffmpeg-python>=0.2.0',
        'imageio>=2.31.1',
        'imageio-ffmpeg>=0.4.8',
        'tqdm>=4.46.0',
        'cachetools>=4.2.2',
    ],
    entry_points={
        'console_scripts': [
            'zunda = zunda.main:main',
        ],
    },
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
    ],
)
