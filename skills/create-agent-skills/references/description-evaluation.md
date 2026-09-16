# Evaluate AI Agent Skill selection and task execution

Write the description around a user intent: when to use the skill, what
specialized outcome it provides, and which tempting neighboring task is outside
scope. Prefer concrete nouns and verbs to “expert,” “comprehensive,” or “always
use.” Do not add unrelated keywords to increase activation.

Use only metadata visible to the target client's discovery mechanism when
testing routing. Check that client rather than assuming every host exposes
exactly the same metadata or loads skills identically. A frontmatter-only review
can reveal ambiguity, but actual activation is a client/model behavior.

Create realistic positive and near-miss prompts, including short/long requests,
indirect vocabulary, similar unsupported tasks, and explicit scope exclusions.
For an individual description being optimized, roughly twenty varied queries are
a useful starting set, not a correctness threshold. Reserve cases not used to
tune the description. Repeat actual runs to expose stochastic behavior; record
model/client/version, enabled catalog, prompt, observed loaded skills, and
outcome.

Judge false negatives and false positives separately. A skill loading on every
prompt is not good recall. Test neighboring skills together to expose
competition, and allow no-skill cases. Avoid forcing “exactly one skill” when a
genuinely composite request needs several independent capabilities.

For output quality, use representative tasks with observable assertions: files
produced, prohibited changes avoided, actual test outcomes, correct error
handling, and preservation of the contract. Compare the same task and
environment with and without the skill. Keep grading independent of the skill's
claimed intent where feasible. Inspect observable actions and artifacts; do not
demand private chain-of-thought transcripts.

Report static validation, manual review, executed snippets, activation trials,
and end-to-end task evaluations as distinct evidence classes. Do not label an
unexecuted test set “passed,” or infer a one-shot success guarantee from a lint
score. Add tests for observed failures rather than accumulating speculative
rules indefinitely.

Sources: [optimizing descriptions][ref-optimizing-descriptions], [evaluating
output quality][ref-evaluating-output-quality].

[ref-optimizing-descriptions]: https://agentskills.io/skill-creation/optimizing-descriptions
[ref-evaluating-output-quality]: https://agentskills.io/skill-creation/evaluating-skills
