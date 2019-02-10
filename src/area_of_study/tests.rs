use super::*;
use crate::rules::{count_of, course, req_ref};
use indexmap::indexmap;

#[test]
fn deserialize() {
	let data = r#"
name: Exercise Science
type: major
degree: "Bachelor of Arts"
catalog: 2015-16

result:
  count: all
  of:
    - requirement: Core
    - requirement: Electives

requirements:
  Core:
    result:
      count: all
      of:
        - BIO 143
        - BIO 243
        - ESTH 110
        - ESTH 255
        - ESTH 374
        - ESTH 375
        - ESTH 390
        - PSYCH 125

  Electives:
    result:
      count: 2
      of:
        - ESTH 290
        - ESTH 376
        - PSYCH 230
        - NEURO 239
        - PSYCH 241
        - PSYCH 247
        - {count: 1, of: [STAT 110, STAT 212, STAT 214]}
"#;

	let expected_struct = AreaOfStudy {
		area_name: "Exercise Science".to_string(),
		area_type: AreaType::Major {
			degree: "Bachelor of Arts".to_string(),
		},
		catalog: "2015-16".to_string(),
		institution: None,
		result: Rule::CountOf(count_of::Rule {
			count: count_of::Counter::All,
			of: vec![
				Rule::Requirement(req_ref::Rule {
					requirement: "Core".to_string(),
					optional: false,
				}),
				Rule::Requirement(req_ref::Rule {
					requirement: "Electives".to_string(),
					optional: false,
				}),
			],
		}),
		attributes: None,
		requirements: [
			(
				"Core".to_string(),
				Requirement {
					message: None,
					department_audited: false,
					registrar_audited: false,
					contract: false,
					save: vec![],
					requirements: indexmap! {},
					result: Some(Rule::CountOf(count_of::Rule {
						count: count_of::Counter::All,
						of: vec![
							Rule::Course(course::Rule {
								course: "BIO 143".to_string(),
								..Default::default()
							}),
							Rule::Course(course::Rule {
								course: "BIO 243".to_string(),
								..Default::default()
							}),
							Rule::Course(course::Rule {
								course: "ESTH 110".to_string(),
								..Default::default()
							}),
							Rule::Course(course::Rule {
								course: "ESTH 255".to_string(),
								..Default::default()
							}),
							Rule::Course(course::Rule {
								course: "ESTH 374".to_string(),
								..Default::default()
							}),
							Rule::Course(course::Rule {
								course: "ESTH 375".to_string(),
								..Default::default()
							}),
							Rule::Course(course::Rule {
								course: "ESTH 390".to_string(),
								..Default::default()
							}),
							Rule::Course(course::Rule {
								course: "PSYCH 125".to_string(),
								..Default::default()
							}),
						],
					})),
				},
			),
			(
				"Electives".to_string(),
				Requirement {
					message: None,
					department_audited: false,
					registrar_audited: false,
					contract: false,
					save: vec![],
					requirements: indexmap! {},
					result: Some(Rule::CountOf(count_of::Rule {
						count: count_of::Counter::Number(2),
						of: vec![
							Rule::Course(course::Rule {
								course: "ESTH 290".to_string(),
								..Default::default()
							}),
							Rule::Course(course::Rule {
								course: "ESTH 376".to_string(),
								..Default::default()
							}),
							Rule::Course(course::Rule {
								course: "PSYCH 230".to_string(),
								..Default::default()
							}),
							Rule::Course(course::Rule {
								course: "NEURO 239".to_string(),
								..Default::default()
							}),
							Rule::Course(course::Rule {
								course: "PSYCH 241".to_string(),
								..Default::default()
							}),
							Rule::Course(course::Rule {
								course: "PSYCH 247".to_string(),
								..Default::default()
							}),
							Rule::CountOf(count_of::Rule {
								count: count_of::Counter::Number(1),
								of: vec![
									Rule::Course(course::Rule {
										course: "STAT 110".to_string(),
										..Default::default()
									}),
									Rule::Course(course::Rule {
										course: "STAT 212".to_string(),
										..Default::default()
									}),
									Rule::Course(course::Rule {
										course: "STAT 214".to_string(),
										..Default::default()
									}),
								],
							}),
						],
					})),
				},
			),
		]
		.iter()
		.cloned()
		.collect(),
	};

	let actual: AreaOfStudy = serde_yaml::from_str(&data).unwrap();
	assert_eq!(actual, expected_struct);
}
