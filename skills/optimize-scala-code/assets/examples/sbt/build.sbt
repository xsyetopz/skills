// Builds the same sources as the scala-cli harness: ../constructs holds
// the code under test and ../bench the JMH classes.
scalaVersion := "3.8.4"
scalacOptions ++= Seq("-deprecation", "-feature", "-unchecked")
libraryDependencies +=
  "org.scala-lang.modules" %% "scala-parallel-collections" % "1.2.0"
Compile / unmanagedSourceDirectories ++= Seq(
  baseDirectory.value / ".." / "constructs",
  baseDirectory.value / ".." / "bench"
)
enablePlugins(JmhPlugin)
// JMH takes a lock file in java.io.tmpdir; JMH_TMPDIR gives each run its
// own directory on a shared machine.
Jmh / run / javaOptions ++=
  sys.env.get("JMH_TMPDIR").map(d => s"-Djava.io.tmpdir=$d").toSeq
