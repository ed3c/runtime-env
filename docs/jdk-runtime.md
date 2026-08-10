# JDK runtime planes

## Separate contracts

The local and cloud Java build planes intentionally share only the feature
release:

| Plane | Profile | Inputs | Physical meaning |
|---|---|---|---|
| local macOS | `java-build-local` | `JAVA_HOME`, `JAVA_VERSION=21` | An existing complete JDK on the host; the path never migrates into another repository or cloud runner. |
| cloud runtime | `java-build-cloud` | `JAVA_VERSION=21`, `CLOUD_JDK_DISTRIBUTION=temurin` | Provider-neutral selectors that a cloud adapter maps to its own JDK setup mechanism. |

`JAVA_HOME` is therefore `local-only`, while `JAVA_VERSION` is `portable` and
`CLOUD_JDK_DISTRIBUTION` is `cloud-runtime`. A cloud adapter may choose another
cataloged distribution later; it must not reuse an Android Studio application
path from macOS.

## Local JBR candidate

Android's official JDK guidance describes JetBrains Runtime as an enhanced JDK
distributed with Android Studio and states that terminal Gradle builds use
`JAVA_HOME` when set. The tracked catalog does not hard-code the application
installation path. On a host where Android Studio is installed, place the
resolved JBR home only in the canonical untracked dotenv:

```bash
./runtime-env local-env reconcile
./runtime-env local-env set-path \
  --name JAVA_HOME \
  --path "/Applications/Android Studio.app/Contents/jbr/Contents/Home"
./runtime-env workload run \
  --id local-jdk-verify \
  --entrypoint verify \
  --target-root /Users/neon/runtime-env \
  --env-file /Users/neon/runtime-env/.env
```

The workload does not trust `java -version` alone. It requires executable
`java` and `javac`, checks that both match `JAVA_VERSION`, compiles a temporary
class, runs it, and emits only metadata plus a private receipt.

## Cloud projection

For GitHub Actions, a consumer can map the cloud profile to the official Java
setup action without importing the local dotenv:

```yaml
- uses: actions/setup-java@v5
  with:
    distribution: temurin
    java-version: "21"
```

The exact action version remains the consumer repository's responsibility and
should be pinned according to that repository's supply-chain policy.

## License boundary

JetBrains describes JBR as an OpenJDK fork and publishes GPLv2 license and
assembly-exception files in its source repository. Using the bundled JDK to run
Gradle or compile an independent commercial application does not by itself
make that application's source a derivative of the JDK. Redistributing or
modifying JBR is a different act and can carry source, notice, and license
obligations. This repository records the runtime boundary; it is not legal
advice and does not claim an unconditional exemption.

Official anchors:

- [Android: Java versions in Android builds](https://developer.android.com/build/jdks)
- [JetBrains Runtime source repository](https://github.com/JetBrains/JetBrainsRuntime)
- [JetBrains Runtime GPLv2 license](https://github.com/JetBrains/JetBrainsRuntime/blob/master/LICENSE)
- [JetBrains Runtime assembly exception](https://github.com/JetBrains/JetBrainsRuntime/blob/master/ASSEMBLY_EXCEPTION)
- [GitHub `actions/setup-java`](https://github.com/actions/setup-java)
