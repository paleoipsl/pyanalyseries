## Updating the source code

### Standard update

```bash
git pull
```

---

### When `git pull` fails

If you see an error such as:

- *"Your local changes would be overwritten"*
- *"Please commit or stash your changes"*

this means that some files were modified locally.

---

### Reset local changes

If you do not need your local modifications, run:

```bash
git fetch
git reset --hard origin/main
```

Then update again:

```bash
git pull
```

---

### Alternative (reinstall)

```bash
cd ..
rm -rf PyAnalySeries
git clone https://github.com/PaleoIPSL/PyAnalySeries.git
cd PyAnalySeries
```

---

## User data location

User data (projects, input files, results, exports, etc.) should **not be stored inside the installation directory**.

Updating or reinstalling the application may overwrite or delete files located in the repository folder.

It is recommended to keep your data in a separate directory outside of PyAnalySeries.
