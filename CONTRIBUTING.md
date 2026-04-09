# Contributing to secure-messenger

Thank you for taking the time to contribute! Here's everything you need to know.

---

## Ways to Contribute

- 🐛 **Report bugs** — open a Bug Report issue
- 💡 **Suggest features** — open a Feature Request issue
- 🔧 **Fix bugs or improve code** — fork, branch, PR
- 📝 **Improve documentation** — even typo fixes are welcome
- 🧪 **Add tests** — especially integration tests

---

## Development Setup

```bash
git clone https://github.com/danshu3007-lang/secure-messenger
cd secure-messenger

python3 -m venv .venv
source .venv/bin/activate
pip install .

bash tests/certs/gen_test_certs.sh
MESSENGER_CERT_DIR=tests/certs pytest tests/unit/ -v
```

All 23 tests should pass before you start making changes.

---

## Branching

- `main` — stable, tested code only
- `feature/your-feature-name` — for new features
- `fix/short-description` — for bug fixes

Always branch off `main`.

```bash
git checkout -b feature/your-feature-name
```

---

## Commit Messages

Use clear, descriptive commit messages. Follow this pattern:

```
type: short description (max 72 chars)

Optional longer explanation if needed.
```

**Types:**
- `feat:` — new feature
- `fix:` — bug fix
- `docs:` — documentation only
- `test:` — adding or updating tests
- `refactor:` — code change with no feature/fix
- `chore:` — build scripts, dependencies, etc.

**Good examples:**
```
feat: add --timeout flag to rcv command
fix: handle certificate error when ca.crt is missing
docs: add mTLS usage example to README
test: add unit tests for crypto key rotation
```

**Avoid:**
```
fix
update stuff
done
wip
```

---

## Pull Request Process

1. Fork the repo and create your branch from `main`
2. Make your changes
3. Add or update tests if applicable
4. Run the full test suite — all tests must pass
5. Open a PR with a clear title and description
6. Reference any related issues with `Closes #123`

PRs that break tests or add untested code to security-sensitive paths will not be merged.

---

## Security Vulnerabilities

**Do not open a public issue for security vulnerabilities.**

If you find a security issue, please report it privately via GitHub's [Security Advisories](https://github.com/danshu3007-lang/secure-messenger/security/advisories/new) feature.

---

## Code Style

- Follow PEP 8
- Use descriptive variable and function names
- Add docstrings to public functions
- Comments should explain *why*, not *what*
- Keep functions small and focused

---

## Questions?

Open a [Discussion](https://github.com/danshu3007-lang/secure-messenger/discussions) if you have questions before opening a PR.
