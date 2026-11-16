# Candidate System Comparison

## Objective

Select an open-source configurable system for studying configuration-option
interactions. The initial experiment will generate 2-way covering arrays
using NIST ACTS and run the selected system's existing test suite under
each configuration.

Our team will study a different system from the other project group.
Their curl-based work serves as a methodological reference.

## Selection Criteria

- Accessible source code and configuration documentation.
- Identifiable options, finite value domains, and dependencies.
- Availability of an open test suite maintained by the system's developers.
- Feasibility of automated configuration, building, and testing.
- Feasibility of collecting test outcomes and code coverage.
- Setup effort within the project timeline.

## Candidate Comparison

| System | Strengths | Risks and Required Checks | Current Status |
|---|---|---|---|
| SQLite | The team has prior experience from a runtime PRAGMA prototype. Public Tcl tests are included in the source tree. Compile-time options provide another configuration dimension to investigate. | The existing prototype did not use SQLite's own test suite. We must identify suitable compile-time options, verify their dependencies, and check test-suite compatibility. Coverage collection also requires validation. The proprietary TH3 suite is outside our scope. | Candidate for the first feasibility check; selection is not yet final. |
| BusyBox | Build-time selection of utilities and features provides a configurable system. Its .config file records build selections. | We must select a coherent feature subset, inspect its dependencies, and verify the availability and applicability of existing tests. Automated result extraction and coverage collection require validation. | Alternative candidate pending feasibility investigation. |

## Reference System: curl

The other project group uses curl. We therefore exclude curl from our
system selection while retaining it as a reference for:

- Configuration-model documentation.
- Automated build and test execution.
- Per-configuration result reporting.
- Before-and-after evaluation of generated tests.

Their implementation and reported measurements are not our results.

## Next Step: SQLite Feasibility Check

We will investigate SQLite first because the team already has experience
with its runtime configuration options.

This does not establish that SQLite is the best candidate. The initial
prototype only demonstrated small generated checks under selected PRAGMA
settings; it did not establish compatibility with SQLite's own test suite.

The feasibility check will:

1. Pin a SQLite source version and record the execution environment.
2. Build a baseline configuration and run its public Tcl test suite.
3. Preserve test logs and identify how outcomes are reported.
4. Verify line and function coverage collection.
5. Identify a small set of compile-time options with source evidence.
6. Change one selected option, rebuild, and repeat the test workflow.
7. Record limitations before making the final system selection.

If these checks reveal major obstacles, we will investigate BusyBox
using the same criteria.

## Configuration Scope

The previous PRAGMA-based model will remain documented as preliminary work.

For the next experiment, we will investigate compile-time options.
The earlier runtime model will not be treated as a validated compile-time
model or transferred directly into ACTS.

After selecting the system and validating its model, we will generate
a constrained 2-way covering array and run the existing test suite
under each generated configuration.

## Evidence Status

This comparison is based on documentation and the team's previous prototype.
We have not yet performed a comparative build, test, or coverage experiment
on SQLite and BusyBox.

No measured ranking of execution time, coverage, or setup effort is claimed.

## Sources

- SQLite compile-time options:
  https://sqlite.org/compile.html
- SQLite testing documentation:
  https://sqlite.org/testing.html
- BusyBox configuration and build documentation:
  https://busybox.net/FAQ.html
- curl test-suite overview, used as a methodological reference:
  https://curl.se/dev/tests-overview.html

## Related Student Work

https://github.com/ebrarguclu/ENS-491-agentic-config-testing

This repository was reviewed as a reference for experimental workflow
and reporting. Any reuse of code or other material will be explicitly
attributed.
