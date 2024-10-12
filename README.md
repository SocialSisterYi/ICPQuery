# ICPQuery

ICPQuery is a CLI tool for query keyword in [**China MIIT ICP Website**](https://beian.miit.gov.cn) to get ICP Record.

It is also Python library that can be invoked by single async function.

## Feature

- The ICP record types can be queried are `domain`、`APP`、`FastAPP`、`MiniAPP`.
- **Keyword** to be querying what can be domain name / APP name / natural name.
- Automatically passing click seqence CAPTCHA, based on OpenCV and trained DNN model.
- Terminal-UI for show querying progress and record data tables.

## Installation

### Install via pypi

The release of `icpquery` is distributed on PyPi(Python Version >= 3.10).

```bash
pip install icpquery
```

### Install from source (whl package)

1. Make sure your system already installed **Python >= 3.10** and **poetry**

2. Download package or clone this repository

3. build and install

```bash
cd ICPQuery
poetry install
poetry build -f wheel
pip install dist/icpquery-xxx.whl
```

## Usage

To show results list with TUI use:

```bash
icpquery 'baidu.com'
```

To output json/plain to stdo use:

```bash
icpquery -f json 'baidu.com'
```
