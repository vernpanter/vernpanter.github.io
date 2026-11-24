# Work on the code

Install [uv](https://docs.astral.sh/uv/) and Ruby 3.3 (`brew install ruby@3.3` on
MacOS), then setup the repo:

```
make setup
```

Run every check that CI runs:

```
make check
```

Start a local copy of the site on port 40100:

```
make serve
```
