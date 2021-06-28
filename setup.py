from setuptools import setup, find_packages

# Run pip install -e .
setup(name='poke_rl',
      version='0.0',
      description='Reinforcement Learning bot for pokemon Showdown simulator.',
      author='Fabien Couthouis - Alexandre Heuillet',
      packages=find_packages(),
      zip_safe=False)
