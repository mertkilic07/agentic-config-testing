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
| Apache ZooKeeper | Documented server configuration options expose interactions involving timing, sessions, and synchronization. The project includes its own tests and a Maven-based build workflow. It offers a distributed-system alternative to SQLite and BusyBox. | Numeric settings require justified finite value domains for ACTS. We must verify that generated configurations are applied to test-created servers rather than overridden by test fixtures. Multi-server tests may introduce additional orchestration and timing variability; coverage collection also requires validation. | Alternative candidate pending feasibility investigation. |

## Configuration Characteristics

The candidates offer different configuration mechanisms:

- **SQLite:** Compile-time options and runtime settings, including PRAGMAs.
  Our initial feasibility investigation will focus on compile-time options.
- **BusyBox:** Build-time selection of utilities and optional features,
  recorded in a .config file.
- **Apache ZooKeeper:** Server settings supplied through configuration files
  and, for supported options, Java system properties. Some settings affect
  interactions between servers.

The configuration model must reflect the selected system's actual behavior.
Numeric options will require a documented selection of representative values.
Dependencies and constraints will require evidence from documentation,
source code, or targeted execution checks.

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
2. Build a baseline configuration and run its public Tcl tests, recording
   the exact test target and scope.
3. Preserve test logs and identify how outcomes are reported.
4. Verify line and function coverage collection.
5. Identify a small set of compile-time options with source evidence.
6. Change one selected option, verify the resulting build configuration,
   and repeat the test workflow.
7. Record limitations before making the final system selection.

If these checks reveal major obstacles, we will investigate BusyBox
and Apache ZooKeeper using the same criteria.

## Planned Experimental Workflow

After selecting the system, we will:

1. Define the configuration model: options, values, and constraints.
2. Verify the model against documentation, source code, and targeted checks.
3. Generate a constrained 2-way covering array using NIST ACTS.
4. Independently check that the generated array covers all valid pairs
   within the modeled configuration space.
5. Build or configure the system for each generated row.
6. Verify that the effective configuration matches the intended settings.
7. Run the system's existing test suite and preserve execution logs.
8. Collect test outcomes and code coverage for each configuration.

Configuration pair coverage and code coverage will be reported separately.
Neither metric alone establishes that the tests adequately check the
behavior of an interaction.

Build failures, test failures, skipped tests, and measurement failures
will also be recorded separately.

## Relationship to the Previous Prototype

The previous PRAGMA-based SQLite model will remain documented as
preliminary work.

For the next SQLite experiment, we will investigate compile-time options.
The earlier runtime model will not be treated as a validated compile-time
model or transferred directly into ACTS.

The main methodological change is to execute the selected system's own
tests rather than relying only on small generated checks.

## Evidence Status

This comparison is based on documentation and the team's previous prototype.
We have not yet performed a comparative build, test, or coverage experiment
on SQLite, BusyBox, and Apache ZooKeeper.

No measured ranking of execution time, coverage, or setup effort is claimed.
The risks listed above are considerations to investigate, not experimentally
confirmed limitations.

The final selection and its supporting feasibility results will be recorded
in docs/selection.md.

## Sources

### SQLite

- Compile-time options:
  https://sqlite.org/compile.html
- Testing documentation:
  https://sqlite.org/testing.html

### BusyBox

- Configuration and build documentation:
  https://busybox.net/FAQ.html

### Apache ZooKeeper

- Administrator's Guide:
  https://zookeeper.apache.org/doc/current/zookeeperAdmin.html
- Getting Started Guide:
  https://zookeeper.apache.org/doc/current/zookeeperStarted.html
- Project README:
  https://github.com/apache/zookeeper/blob/master/README.md
- Build and test packaging notes:
  https://github.com/apache/zookeeper/blob/master/README_packaging.md

### NIST ACTS

- Tools and downloads:
  https://csrc.nist.gov/projects/combinatorial-testing-for-ai-enabled-systems/downloadable-tools

### curl — Methodological Reference

- Test-suite overview:
  https://curl.se/dev/tests-overview.html

Documentation URLs may track current development. During implementation,
we will pin the selected system's version and record version-specific
source references for the configuration model.

## Related Student Work

https://github.com/ebrarguclu/ENS-491-agentic-config-testing

This repository was reviewed as a reference for experimental workflow
and reporting. Any reuse of code or other material will be explicitly
attributed.
