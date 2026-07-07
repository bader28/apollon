# Apollon
Apollon is a Python framework for audio feature extraction and music similarity
estimation. It includes subpackages for

* Audio feature extraction
* Hidden Markov Models
* Self-Organizing Map

This is the fork maintained by **Rolf Bader** (canonical repository on
[Codeberg](https://codeberg.org/rbader/apollon)). It is the foundation of the
apollon / chainsaddiction / comsar stack. For the full manual and installation
guide covering all three packages see the
[comsar repository](https://codeberg.org/rbader/comsar).

## 1. Installation
### 1.1 Install from PyPI (recommended, no compiler needed)
Pre-compiled wheels are provided for **Windows, macOS and Linux**
(CPython 3.9–3.13). Just run:

```
pip install bader-apollon
```

The import name is unchanged — you still write `import apollon` in your code.

### 1.2 Install from source
Building from source requires a C compiler (MSVC Build Tools on Windows, the
Xcode Command Line Tools on macOS, gcc/clang on Linux) plus NumPy:

```
pip install .
```

## 2. Documentation
See the [comsar manual](https://codeberg.org/rbader/comsar) for the full
documentation of the whole stack.
