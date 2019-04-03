use crate::area_of_study::AreaOfStudy;
use crate::rules;
use std::iter;

pub trait Solvable {
    fn solutions(&self) -> Solution;
}

#[derive(Clone)]
pub enum Solution {
    Course(CourseSolution),
    Both(BothSolution),
    Either(EitherSolution),
    Count(CountSolution),
    Given(GivenSolution),
    Action(ActionSolution),
    Save(SaveSolution),
    Requirement(RequirementSolution),
    Area(AreaSolution),
}

#[derive(Clone)]
pub struct CourseSolution{rule: CourseInstance}

#[derive(Clone)]
pub struct BothSolution{rule: rules::both::Rule}
#[derive(Clone)]
pub struct EitherSolution{rule: rules::either::Rule, index: usize}

#[derive(Clone)]
pub enum SolutionIterator {
    Course(CourseIterator),
    Both(BothIterator),
    Either(EitherIterator),
    Count(CountIterator),
    Given(GivenIterator),
    Action(ActionIterator),
    Save(SaveIterator),
    Requirement(RequirementIterator),
    Area(AreaIterator),
}

type CountIterator = std::vec::IntoIter<Solution>;
type EitherIterator = iter::Chain<iter::Once<Solution>, iter::Once<Solution>>;
type BothIterator = iter::Once<Solution>;
type CourseIterator = iter::Once<Solution>;

