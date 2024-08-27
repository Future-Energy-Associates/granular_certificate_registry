# Contributing to the EnergyTag Demonstration Registry

## Principles



## Create a pull request (PR)

Make changes on a dedicated branch off the main branch: `git checkout -b {my-feature-branch}`

0. Feel free to raise a PR before development is complete - ensure that the PR is marked as a `draft`
1. Typecheck and format your code locally using `make format && make typecheck` - make any required changes (Or ideally, install the pre-commit hook so that this runs automatically everytime you commit. See [here](./DEVELOPMENT.md#pre-commits-for-linting-formatting-and-type-checking) for details)
2. Ensure tests all pass using `make test`
3. Ensure that the feature branch is up-to-date with the main branch (`git merge dev`)
4. Ensure PR has enough detail to understand what the feature does
5. Request review from one of the team
6. Optionally talk reviewer through changes if complex
7. Make any required changes and request re-review
8. Once review is approved - merge via GitHub
9. Delete feature branch

## Commit messages

We follow the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0-beta.4/#summary) specification for formatting our commit message. The benefit herr is that commit messages will contain the correct keywords (e.g. feat:, fix: etc) to trigger the [semantic versioning](./DEVELOPMENT.md#versioning) we have enabled on this repository.
