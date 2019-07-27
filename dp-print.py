import json
import sys
import argparse

from degreepath.stringify import print_result
from degreepath import CourseInstance


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("json_output", action='store')
    parser.add_argument("student_file", action='store')
    args = parser.parse_args()

    with open(args.json_output, 'r', encoding="utf-8") as infile:
        data = json.load(infile)

    with open(args.student_file, 'r', encoding="utf-8") as infile:
        student = json.load(infile)

    transcript = []
    for row in student["courses"]:
        instance = CourseInstance.from_dict(**row)
        if instance:
            transcript.append(instance)
        else:
            print("error loading course into transcript", row, file=sys.stderr)

    summary = "\n".join(print_result(data, transcript=transcript))
    print(summary)


if __name__ == "__main__":
    main()
