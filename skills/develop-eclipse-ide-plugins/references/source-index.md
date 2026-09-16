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
| [Eclipse Platform Plug-in Developer Guide](https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/guide/) | Primary platform development guide. |
| [SWT threading](https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/guide/swt_threading.htm) | SWT display-thread rules. |
| [Tycho](https://tycho.eclipseprojects.io/) | Maven/Tycho target-platform build and test documentation. |
| [download.eclipse.org: index.html](https://download.eclipse.org/eclipse/downloads/drops4/R-4.40-202606010713/index.html) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [eclipse.dev: swt](https://eclipse.dev/eclipse/swt/) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [GitHub source: eclipse-tycho/tycho — pom.xml](https://github.com/eclipse-tycho/tycho/blob/tycho-5.0.4/demo/testing/tycho/standalone/test/pom.xml) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [GitHub: eclipse-tycho/tycho/releases/tag/tycho-5.0.4](https://github.com/eclipse-tycho/tycho/releases/tag/tycho-5.0.4) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [help.eclipse.org: index.jsp](https://help.eclipse.org/latest/index.jsp) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [help.eclipse.org: editor.htm](https://help.eclipse.org/latest/topic/org.eclipse.pde.doc.user/guide/tools/editors/manifest_editor/editor.htm) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [help.eclipse.org: jface resources.htm](https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/guide/jface_resources.htm) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [help.eclipse.org: p2 director.html](https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/guide/p2_director.html) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [help.eclipse.org: runtime jobs.htm](https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/guide/runtime_jobs.htm) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [help.eclipse.org: runtime jobs rules.htm](https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/guide/runtime_jobs_rules.htm) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [help.eclipse.org: workbench cmd.htm](https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/guide/workbench_cmd.htm) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [help.eclipse.org: package summary.html](https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/reference/api/org/eclipse/core/runtime/jobs/package-summary.html) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [help.eclipse.org: TextSelection.html](https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/reference/api/org/eclipse/jface/text/TextSelection.html) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [help.eclipse.org: Color.html](https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/reference/api/org/eclipse/swt/graphics/Color.html) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [help.eclipse.org: ITextEditorExtension2.html](https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/reference/api/org/eclipse/ui/texteditor/ITextEditorExtension2.html) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [help.eclipse.org: launcher ini.html](https://help.eclipse.org/latest/topic/org.eclipse.platform.doc.isv/reference/misc/launcher_ini.html) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [tycho.eclipseprojects.io: TestingBundles.html](https://tycho.eclipseprojects.io/doc/5.0.4/TestingBundles.html) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [tycho.eclipseprojects.io: latest](https://tycho.eclipseprojects.io/doc/latest/) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [tycho.eclipseprojects.io: TargetPlatform.html](https://tycho.eclipseprojects.io/doc/latest/TargetPlatform.html) | Use for the exact target version or source revision; verify applicability before copying an API or command. |

## Updating this reference

Update a link only after confirming the replacement covers the same contract. If
a source disappears, preserve the rule supported by local evidence and mark the
external verification gap; do not invent a new behavior from memory.
