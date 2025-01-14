[![PyPI Package latest release](https://img.shields.io/pypi/v/limedev.svg)][1]
[![PyPI Wheel](https://img.shields.io/pypi/wheel/limedev.svg)][1]
[![Supported versions](https://img.shields.io/pypi/pyversions/limedev.svg)][1]
[![Supported implementations](https://img.shields.io/pypi/implementation/limedev.svg)][1]

# LimeDev <!-- omit in toc -->

LimeDev is collection tools for Python development. These tools are more or less thin wrappers around other packages.

## Table of Contents <!-- omit in toc -->

- [Quick start guide](#quick-start-guide)
    - [The first steps](#the-first-steps)
        - [Installing](#installing)
        - [Importing](#importing)

# Quick start guide

Here's how you can start

## The first steps

### Installing

Install LimeDev with pip

```
pip install limedev
```

### Importing

Import name is the same as install name, `limedev`.

```python
import limedev
```

# Changelog <!-- omit in toc -->

## 0.6.2 2025-01-14 <!-- omit in toc -->

- Changed signature of the benchmarking function
- Best-of sampling on benchmarking function

## 0.6.1 2024-07-17 <!-- omit in toc -->

- Running the benchmakable function once in setup to better accompany numba
- Expanding benchmarking prefixes

## 0.6.0 2024-07-17 <!-- omit in toc -->

### Features <!-- omit in toc -->

#### Readme toolkit <!-- omit in toc -->

- Readme tool now gives the full pyproject dictionary
- readme make tool allows abbreviation

#### Testing toolkit <!-- omit in toc -->

- Benchmarking tools added

## 0.5.0 2024-07-16 <!-- omit in toc -->

- Updated CLI framework
- Support for python 3.9 dropped
- Support for python 3.13 added

## 0.4.1 2023-11-06 <!-- omit in toc -->

- Fixed configs

## 0.4.0 2023-11-06 <!-- omit in toc -->

- Updated profiling structure
- function_cli
- Python version range moved from 3.9 -3.11 to 3.10-3.12

## 0.3.0 2023-08-27 <!-- omit in toc -->

- Change to testing interface

## 0.2.2 2023-08-27 <!-- omit in toc -->

- Fix to performance test deleting previous performance data

## 0.2.1 2023-08-06 <!-- omit in toc -->

- Performance results dump sorting fix

## 0.2.0 2023-08-06 <!-- omit in toc -->

- Bugfixes
- Cleaner structure
- Reworked readme build

## 0.1.0 2023-05-04 <!-- omit in toc -->

- Initial assembly of the tools

[1]: <https://pypi.org/project/limedev> "Project PyPI page"
