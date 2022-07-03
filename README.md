# Shinkansen Python Helpers

See https://docs.shinkansen.tech for user guides.

## Development

With poetry:

    $ poetry install
    $ poetry shell 

Install pre-commit hooks:

    $ pre-commit install

Run tests:

    $ poetry run tests

### Publish a new version

PyPI publishing:

- Bump versions in `pyproject.toml` and `shinkansen/__init__.py`
- Add & commit
- Tag as `vX.Y.Z`
- Push
- Then run:

      $ poetry build
      $ poetry publish

### Troubleshooting

If `poetry install` fails on MacOS, it's likely due to the cryptography library
trying to be built from source. The right fix is to figure out why it's trying
to build the library from source instead of downloading a binary wheel. But,
this  could be a workaround to build from source:

   $ brew install rust
   $ brew install openssl
   $ env LDFLAGS="-L$(brew --prefix openssl)/lib" CFLAGS="-I$(brew --prefix openssl)/include" poetry install
