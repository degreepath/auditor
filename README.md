# Degreepath, the automated degree auditor

> Gobbldygook lives!

Degreepath is a tool to perform automated, comprehensive, and fast degree audits.

**Automated**: (eventually) A web interface, for reviewing the status of a cohort of students and for running reports

**Comprehensive**: Just checking degree audits? Nah. How about running graduation, general education, major, and concentration/minor audits, all at once?

**Fast**: (eventually) And of course, this only makes sense to run if it's faster than doing the checks by hand. Luckily, computers are fast, and they can do lots of things at once!

---

Requires Python 3.6+.

```shell script
$ python3 -m venv ./venv
$ source ./venv/bin/activate  # or ./venv/bin/activate.fish
$ pip install -r requirements.txt
$ python3 -m dp --help
```

To run tests:

```shell script
$ pytest  # or, with coverage, pytest --cov=dp
```

Other commands:

## CLI

```shell script
$ python3 -m dp --help
```

The main CLI entry point; see `--help`.

Basic usage is as follows:

```shell script
# somehow get a student JSON file; documentation coming at some point
# area.yaml can be any .yaml file in the stolaf-areas repository
$ python3 -m dp --student <student.json> --area <area.yaml>
```

## Batch Job Server

The `dp.server` module handles sorting through the queued jobs, both batched and one-off what-ifs.

Basic usage is as follows:

```shell script
# start listening for events from postgres
$ python3 -m dp.server &
# fetch the next batch of students to audit from SIS and queues them in postgres
$ python3 -m dp.server.batch
# or, run a one-off what-if audit
$ python3 -m dp.server.whatif --student <file> --code <code> --catalog <catalog>
```

The `dp.server.audit` module encapsulates driving the auditor and storing the final result into postgres.

## Misc. Scripts

- You can pair up `python3 -m dp.bin.index <QUERY> | python3 -m dp.bin.batch` to run batches of audits quickly on a folder of student files.
- `python3 -m dp.bin.discover <area-file>` will give you a list of the bucket references and static course references contained within.
- `python3 -m dp.bin.expand <student-file>` will print (student_file, area_file) pairs to stdout, one for each area in the student.
- `python3 -m dp.bin.print <student-file> <output-json>` will print the same output that `-m dp` generates.
- `python3 -m dp.bin.validate <area-file>` will validate that an area specification is syntactically valid.

## Fancier CLI

```shell script
$ python3 -m dp.testbed --help
```

Allows eas[ier] benchmarking of changes against the stable branch.

Usage:

```shell script
$ python3 -m dp.testbed fetch
$ python3 -m dp.testbed baseline
$ python3 -m dp.testbed branch <name>
$ python3 -m dp.testbed compare <name>
```

---

You may notice that there are three `requirements*.txt` files. I split them apart so that I could install the dependencies easily.

| filename                  | why                                          |
| ------------------------- | -------------------------------------------- |
| `requirements.txt`        | Common runtime dependencies                  |
| `requirements-dev.txt`    | Development dependencies - pytest, mypy, etc |
| `requirements-server.txt` | Database and error logging dependencies      |

---

```
Copyright (C) 2019  Hawken MacKay Rives

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
```
