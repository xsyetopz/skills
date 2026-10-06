# Java, Kotlin, and Scala

## Contents

- [Visibility](#visibility)
- [Java](#java)
- [Kotlin](#kotlin)
- [Scala 3](#scala-3)

## Visibility

Start at the narrowest level and widen for a real caller.

| Caller | Java | Kotlin | Scala 3 |
| --- | --- | --- | --- |
| Same class | `private` | `private` | `private` |
| Same file | nested `private` type | `private` top level | `private` top level |
| Same package | package-private | `internal` is module-wide | `private[pkg]` |
| Subclasses | `protected` | `protected` (needs `open`) | `protected` |
| Everyone | `public` | default | default |

Tests go in the mirrored test tree in the same package:
`src/test/java`, `src/test/kotlin`, or `src/test/scala`.

## Java

1. `package`, then imports, with no wildcard imports unless the project uses them.
1. One top-level type per file, named for the file.
1. Inside the type: constants (`public`, `protected`, package, `private`), fields, constructors,
   methods grouped by role (public first), then nested types.
1. A helper used only here is a `private static` nested type, not a second top-level type.

```java
package com.example.component;

import java.util.List;

public final class PublicType {
    public static final int PUBLIC_CONSTANT = 1;
    private static final int PRIVATE_CONSTANT = 3;

    private final List<Integer> values = List.of(PRIVATE_CONSTANT);

    public PublicType() {}

    public int publicMethod() {
        return privateMethod();
    }

    protected void protectedMethod() {}

    void packageMethod() {}

    private int privateMethod() {
        return new Helper().first(values);
    }

    private static final class Helper {
        int first(List<Integer> xs) {
            return xs.getFirst();
        }
    }
}
```

## Kotlin

1. `package`, then imports (the standard library defaults need none).
1. File-level constants.
1. The main type, members in role order, `companion object` last.
1. `internal` types, then `private` file-level types.

A library enables explicit API mode (`-Xexplicit-api=strict`), so state `public` there.
`protected` in a final class is a warning, so mark the class `open` or drop `protected`.

```kotlin
package com.example.component

const val PUBLIC_CONSTANT = 1
internal const val MODULE_CONSTANT = 2
private const val PRIVATE_CONSTANT = 3

open class PublicType {
    fun publicMethod() = privateMethod()

    internal fun moduleMethod() {}

    protected fun protectedMethod() {}

    private fun privateMethod() = PRIVATE_CONSTANT
}

internal class InternalType {
    fun run() {}
}

private class FilePrivateType
```

## Scala 3

1. `package`, then imports.
1. Constants in an `object`.
1. Each class or trait, with its companion object immediately after it.
1. Scoped-private types (`private[component]`) last.

```scala
package com.example.component

object Constants:
  val PublicValue = 1
  private val PrivateValue = 2

class PublicType:
  def publicMethod(): Unit = privateMethod()
  protected def protectedMethod(): Unit = ()
  private def privateMethod(): Unit = ()

object PublicType:
  def apply(): PublicType = new PublicType

private[component] class PackageScopedType
```
