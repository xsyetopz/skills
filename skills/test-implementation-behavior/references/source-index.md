# Source index and freshness rules

This index is for source discovery and version checking. It is not a substitute
for the operational rules in `SKILL.md` and the other references. Open the
underlying source; do not treat a search snippet, generated summary, or copied
example as authority.

## Source order

1. Inspect the target repository, installed tool versions, lockfiles, generated
   relationships, and existing validation commands.
1. Use the exact product or language version's official documentation and
   source.
1. Use standards and protocol specifications for normative behavior.
1. Use issue trackers and community reports to discover failure patterns, then
   reproduce the relevant behavior locally before changing production code.

For changing products, record the page or source revision and access date in the
work product when the decision depends on it. Do not silently transfer an API or
limit from another version, fork, operating system, runtime, or hosting tier.

## Primary sources

| Source | Applicability |
| --- | --- |
| [Kent Beck — Canon TDD](https://newsletter.kentbeck.com/p/canon-tdd) | Test-first sequence and independent expectations. |
| [Google Testing Blog — test behaviors, not methods](https://testing.googleblog.com/2014/04/testing-on-toilet-test-behaviors-not.html) | Behavior-focused test design. |
| [Zephyr Twister](https://docs.zephyrproject.org/latest/develop/test/twister.html) | Example of explicit build/emulation/device execution distinctions for Zephyr projects. |
| [cocotb testbenches](https://docs.cocotb.org/en/stable/writing_testbenches.html) | HDL simulation patterns when cocotb matches the project. |
| [automationpanda.com: arrange act assert a pattern for writing good tests](https://automationpanda.com/2020/07/07/arrange-act-assert-a-pattern-for-writing-good-tests/) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [blog.ploeh.dk: from interaction based to state based testing](https://blog.ploeh.dk/2019/02/18/from-interaction-based-to-state-based-testing/) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [clang.llvm.org: AddressSanitizer.html](https://clang.llvm.org/docs/AddressSanitizer.html) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [clang.llvm.org: ThreadSanitizer.html](https://clang.llvm.org/docs/ThreadSanitizer.html) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [docs.cocotb.org: writing testbenches.html](https://docs.cocotb.org/en/v2.0.1/writing_testbenches.html) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [docs.pact.io: docs.pact.io](https://docs.pact.io/) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [docs.pytest.org: flaky.html](https://docs.pytest.org/en/stable/explanation/flaky.html) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [hypothesis.readthedocs.io: latest](https://hypothesis.readthedocs.io/en/latest/) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [istqb.org: ISTQB CTFL Syllabus v4.0.1.pdf](https://istqb.org/wp-content/uploads/2024/11/ISTQB_CTFL_Syllabus_v4.0.1.pdf) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [llvm.org: LibFuzzer.html](https://llvm.org/docs/LibFuzzer.html) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [martinfowler.com: mocksArentStubs.html](https://martinfowler.com/articles/mocksArentStubs.html) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [martinfowler.com: GivenWhenThen.html](https://martinfowler.com/bliki/GivenWhenThen.html) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [martinfowler.com: UnitTest.html](https://martinfowler.com/bliki/UnitTest.html) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [packaging.python.org: src layout vs flat layout](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [playwright.dev: best practices](https://playwright.dev/docs/best-practices) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [semver.org: semver.org](https://semver.org/) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [stryker-mutator.io: mutant states and metrics](https://stryker-mutator.io/docs/mutation-testing-elements/mutant-states-and-metrics/) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [test-smell-catalog.readthedocs.io: Overspecified%20Software.html](https://test-smell-catalog.readthedocs.io/en/latest/Code%20related/In%20association%20with%20production%20code/Overspecified%20Software.html) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [testing.googleblog.com: testing on toilet change detector tests.html](https://testing.googleblog.com/2015/01/testing-on-toilet-change-detector-tests.html) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [testing.googleblog.com: just say no to more end to end tests.html](https://testing.googleblog.com/2015/04/just-say-no-to-more-end-to-end-tests.html) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [www.archunit.org: 000 Index.html](https://www.archunit.org/userguide/html/000_Index.html) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [www.informit.com: 0131495054 CH23.pdf](https://www.informit.com/content/images/9780131495050/samplechapter/0131495054_CH23.pdf) | Use for the exact target version or source revision; verify applicability before copying an API or command. |

## Updating this reference

Update a link only after confirming the replacement covers the same contract. If
a source disappears, preserve the rule supported by local evidence and mark the
external verification gap; do not invent a new behavior from memory.
