# Candidate System Comparison

## Objective

Select an open-source configurable system for an initial experiment:
model its configuration space, generate a constrained 2-way covering
array using NIST ACTS, and run the system's existing test suite under
each generated configuration.

## Selection Criteria

- Availability of source code and configuration documentation.
- Identifiable configuration options, values, and dependencies.
- Availability of an existing test suite.
- Feasibility of automated configuration, building, and testing.
- Feasibility of collecting test results and code coverage.
- Setup effort within the initial project timeline.

## Candidates

| System | Strengths | Risks and Required Checks | Initial Assessment |
|---|---|---|---|
| curl | Configurable build-time features and a documented test runner. Suitable for studying protocol and feature combinations. | Some tests require auxiliary servers and external tools. Environment-related skips must be distinguished from configuration-related skips. | Preferred candidate for the first feasibility experiment. |
| SQLite | The team has an initial PRAGMA-based prototype. Public Tcl tests are available in the source tree. | The prototype used small generated checks rather than SQLite's own suite. Runtime settings must be applied to the relevant test connections and checked for overrides. The proprietary TH3 suite is outside our scope. | Strong alternative that builds on previous work. |
| BusyBox | Build-time selection of utilities and features provides a substantial configuration space. Configuration is recorded in a .config file. | A manageable feature subset must be selected. Test-suite applicability and coverage collection must be verified for that subset. | Relevant alternative requiring additional feasibility investigation. |

## Preliminary Decision

We prioritize curl for the first feasibility experiment because its
documented build and test workflow aligns with the required
configuration-by-configuration evaluation.

This is a preliminary selection, not a completed experimental comparison.
We have not yet benchmarked setup time, execution time, or coverage
across these candidates.

Before confirming curl, we will:

1. Pin a source version and record the execution environment.
2. Build a baseline configuration.
3. Run its existing test suite and retain the logs.
4. Collect line and function coverage.
5. Verify that selected configuration changes are reflected in the build.

SQLite remains a potential second evaluation system. BusyBox remains
an alternative if the initial feasibility checks reveal significant
limitations.

## Sources

- curl installation documentation:
  https://curl.se/docs/install.html
- curl test-suite overview:
  https://curl.se/dev/tests-overview.html
- SQLite testing documentation:
  https://sqlite.org/testing.html
- BusyBox configuration and build documentation:
  https://busybox.net/FAQ.html

## Related Student Work

The following repository was reviewed as a reference for the experimental
workflow and reporting structure:

https://github.com/ebrarguclu/ENS-491-agentic-config-testing

Its reported results are not our experimental results.
Any future reuse of code or other material will be explicitly attributed.
