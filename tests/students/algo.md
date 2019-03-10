check multicountable

transcript becomes… HashMap<countable-by, Vec<CourseInstance>>?

{
	ASIAN 130: vec![CourseInstance {}],
	CSCI 121: vec![CourseInstance {}],
	asian_elective: vec![CourseInstance {}],
}

no... because `given:` needs to be able to filter by subject/number/whatever

---

input

```rust
transcript: vec![
	CourseInstance{ course: "ASIAN 130", attributes: ["asian_elective"] },
	CourseInstance{ course: "CSCI 121", attributes: [] },
	CourseInstance{ course: "CSCI 251", attributes: [] },
]
```

after limits

```rust
transcript: vec![
	CourseInstance{ course: "ASIAN 130", attributes: ["asian_elective", "asian_other"] },
	CourseInstance{ course: "CSCI 121", attributes: [] },
]
```

evaluate multicountable

```rust
transcript: vec![
	CourseInstance{ course: "ASIAN 130", attributes: ["asian_elective", "asian_other"] },
	CourseInstance{ course: "CSCI 121", attributes: [] },
]
multicountable: vec![
	MultiMatch(vec![
		HashMap{key: "course", used_by: None, value: "ASIAN 130"},
		HashMap{key: "attribute", used_by: None, value: "asian_elective"},
		HashMap{key: "attribute", used_by: None, value: "asian_other"},
	])
]
matched: vec![]
```

> goes into requirement "Courses"

1. for each item in `of`, until we reach `count`
	1. if it's a course
		1. check `transcript` for the course
		2. if not found, skip because the course wasn't taken
		3. check global limits to see if we can count this course
			1. if we're allowed to count it, continue
		4. if there's a grade restriction, check the grade
			1. if the grade fails, skip this course (TODO: how to indicate the reason for skipping?)
			2. otherwise, continue
		5. either way, do `matched.get` with a reference to the found CourseInstance (returns a MultiMatched)
		6. if there is a match
			1. iterate over `multicountable`
			2. if any MultiMatchable is a strict superset of the found MultiMatched
			3. then add a new MatchedCourse to the MultiMatched with `key: Course, value: $course, used_by: $path_to_rule`
			4. else, skip the course (because it's already been matched)
		7. else, add a match to `matched` with `MatchedCourse{key: Course, value: $course, used_by: $path_to_rule}`
	2. if it's a given
		1. if it's a given:all-courses
			1. if there's a filter, apply the filter to the transcript
				1. create a new, temporary `temp_matched` map as a clone of `matched`
				2. for each course, check `temp_matched` with a reference to the current CourseInstance
				3. if there's a Some, let the result be `got_matched`
					3. iterate over `multicountable`
					2. if any MultiMatchable is a strict superset of `got_matched`
					3. then add a new MatchedCourse to the MultiMatched with `key: Course, value: $course, used_by: $path_to_rule`
					4. else, skip the course (because it's already been matched)
				5. else, add a match to `temp_matched` with `MatchedCourse{key: Course, value: $course, used_by: $path_to_rule}`
			2. check global limits to see if we can count this course
				1. for each course:
					1. if we're allowed to count it, continue
					2. else, skip it (because we've reached one or more applicable limits), and remove it from `temp_matched` (because we aren't using it anymore)
			3. if there's a local limit, apply the limits
				1. for each course:
					1. if we're allowed to count it, continue
					2. else, skip it (because we've reached one or more applicable limits), and remove it from `temp_matched` (because we aren't using it anymore)
			4. run the `do` instructions
				1. if `what:courses`
					1. if `count`: assert that the number of remaining courses is $op than $count
					2. any other rules are invalid
				2. if `what:distinct-courses`
					1. de-duplicate courses by the `course` field (crsid; deptnum; no section)
					2. if `count`: assert that the number of remaining courses is $op than $count
					3. any other rules are invalid
				3. if `what:terms`
					1. extract the `term` in the form `2012-1` from each remaining course
					2. turn the terms into a set of unique terms
					3. if `count`: assert that the number of terms is $op than $count
					4. if `sum`: panic
					5. if `avg`: panic
					6. if `min`: return the smallest term
					7. if `max`: return the largest term
				4. if `what:subjects`
					1. extract the `subject` from each remaining course
						1. split /-delimited subjects into their parts (`AS/RE` => `AS, RE`)
						2. turn all subjects into long-form subjects
					2. turn the subjects into a set of unique subjects
					3. if `count`: assert that the number of subjects is $op than $count
					4. any other rules are invalid
				5. if `what:credits`
					1. extract the `credits` from each remaining course
					2. if `count`: assert that the number of credits is $op than $count
					3. if `sum`: add all credits together; assert that the result is $op than $count
					4. if `avg`: take the average of all credits; assert that the result is $op than $count
					5. if `min`: return the smallest credit value
					6. if `max`: return the largest credit value
				6. if `what:grades`
					1. extract the `grade` from each remaining course
						1. if `no-grade`, remove from the set
						2. if `pass`, remove from the set
						3. if `s/u:s`, remove from the set
						4. if `graded`: extract the letter grade
					2. if `count`: assert that the number of grades is $op than $count
					3. if `sum`: add all grades together; assert that the result is $op than $count
					4. if `avg`: take the average of all grades; assert that the result is $op than $count
					5. if `min`: return the smallest credit value
					6. if `max`: return the largest credit value
		<!-- 2. return the status and `temp_matched` -->
	3. if it's a requirement
		1. fetch the requirement result from the input data
		2. if the requirement passed, pass this rule
		3. if the requirement failed, fail this rule
	4. if it's a container rule
		1. recurse into it and evaluate
		2. combine the `matched` results from each child into a new HashMap of MultiMatcheds
	5. return both the status and the new set of matched courses

TODO: should `used_by` be the path to the Rule or the Requirement that used it?
RESOLVED: the Rule

TODO: applying global limits at the start of execution can result in keeping unusable courses.
FIX: track global limits globally, but apply them at the individual … Rule? level, I guess. That'll take some tweaking of Rules, I think.

TODO: a `given` that outputs grades… how should it handle NG/PF/SU courses?

```rust
transcript: Vec[
	CourseInstance{ course: "ASIAN 130", attributes: ["asian_elective"] },
	CourseInstance{ course: "CSCI 121",  attributes: [] },
]
multicountable: Vec[
	MultiMatchable(HashSet![
		MatchableCourse(Key::Course("ASIAN 130")),
		MatchableCourse(Key::Attribute("asian_elective")),
		MatchableCourse(Key::Attribute("asian_other")),
	])
]
matched: HashMap{
	&CourseInstance => MultiMatched(HashSet![
		MatchedCourse{ key: Key::Course("ASIAN 130"),
		               used_by: Some(Path([
		                    Root,
		                    Requirement("Course"),
		                    Rule(::Of),
		                    Index(1),
		                    Rule(::Course),
		               ])) },
		MatchedCourse{ key: Key::Attribute("asian_elective"),
		               used_by: Some(Path([
		                    Root,
		                    Requirement("Electives")
		                    Rule(::Given),
		               ])) },
	]),
}
limits: Vec[
	LimitState {
		limit: Limit{at_most: 1, where: Filter{subject: SingleValue(NotEqualTo("ASIAN"))}},
		seen: Vec[&CourseInstance{"CSCI 121"}],
	},
	LimitState {
		limit: Limit{at_most: 5, where: Filter{level: SingleValue(LessThan(200))}},
		seen: Vec[
			&CourseInstance{"CSCI 121"},
			&CourseInstance{"CSCI 251"},
			&CourseInstance{"ASIAN 130"},
		],
	}
]
```
