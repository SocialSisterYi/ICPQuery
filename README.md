# ICPQuery

ICPQuery is a CLI tool for query keyword in [**China MIIT ICP Website**](https://beian.miit.gov.cn) to get ICP Record.

It is also Python library that can be invoked by single async function.

## Feature

- The ICP record types can be queried are `domain`、`APP`、`FastAPP`、`MiniAPP`.
- **Keyword** to be querying what can be domain name / APP name / natural name.
- Automatically passing click seqence CAPTCHA, based on OpenCV and trained DNN model.
- Terminal-UI for show querying progress and record data tables.

## Installation

### Installation from source (whl package)

1. Make sure your system already installed **poetry**

2. build and install

```bash
poetry install
poetry build -f wheel
pip install dist/icpquery-xxx.whl
```
