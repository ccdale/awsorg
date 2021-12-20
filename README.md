# AWS Organisations


Run direct from the repo with `poetry run awsorg` or install it with `poetry
build` and then `python3 -m pip install <wheelfile> --user`.  The wheel file
will be in the `dist` directory after the `poetry build` step.

Note: the `region` option is unnecessary at the moment but may be used at a
later date.

It is based on the
[boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/quickstart.html)
library, so popping the profile into the environment under the `AWS_PROFILE` key
will also work.

It uses [poetry](https://python-poetry.org/) to manage it's virtual environment.
If you don't know `poetry` give the once over, it is to `venv` what [John
Inman](https://en.wikipedia.org/wiki/John_Inman) is to [Arthur
Mullard](https://en.wikipedia.org/wiki/Arthur_Mullard)  i.e. fabulous.
```
$ poetry run awsorg --help
Usage: awsorg [OPTIONS] COMMAND [ARGS]...

Options:
  -p, --profile TEXT  The AWS profile (credentials) to use
  -r, --region TEXT   The AWS region to run in
  --help              Show this message and exit.

Commands:
  roots    Display the Root OU ID and ARN for the Organisation.
  summary  Display the OU Tree Summary for the Organisation
  tree
```

```
$ poetry run awsorg --profile orgaccount summary --help
Usage: awsorg summary [OPTIONS]

  Display the OU Tree Summary for the Organisation

OU                 Accounts  Id
---------------  ----------  ----------------
Root                     22
SRE-Test                  1  ou-txxx-xxxxxxxv
SRE                       0  ou-txxx-xxxxxxxn
...
```

```
$ poetry run awsorg -p orgaccount tree --help
Usage: awsorg tree [OPTIONS]

  Display the full OU Tree including child accounts


OU               Account ID    Name
---------------  ------------  ----------------------------------
Root             22
                 500000000005  Dxxxx - Fxxxxx - XXX
                 400000000002  Dxxx - Nxxx Sxxx
                 ...

SRE-Test         1             ou-txxx-xxxxxxxx
                 800000000000  Sxx-SRE

SRE              0             ou-txxx-kxxxxxxx


```
