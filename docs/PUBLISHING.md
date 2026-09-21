# Publishing RefLint

RefLint publishes to PyPI through GitHub Actions using PyPI Trusted Publishing (OIDC). No long-lived PyPI API token is stored in GitHub.

## One-time PyPI setup

Create the project / pending trusted publisher for:

- PyPI project name: `reflint`
- GitHub owner: `coocoomaomao`
- Repository: `RefLint`
- Workflow: `release.yml`
- Environment: `pypi`

The repository workflow already requests `id-token: write` only for the publish job.

## Release process

1. Make sure CI is green on `main`.
2. Create and publish a GitHub Release with the desired tag, for example `v0.1.0`.
3. The `Release` workflow builds wheel + sdist, runs `twine check`, uploads the build artifact, and publishes it to PyPI through OIDC.
4. Verify:
   ~~~bash
   pip install reflint
   reflint --help
   ~~~

## Security

Do not paste PyPI passwords, API tokens, TOTP seeds, QR codes, or recovery codes into issues, pull requests, screenshots, or chat messages.
