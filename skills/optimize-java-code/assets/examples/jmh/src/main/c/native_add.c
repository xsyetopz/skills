/* One tiny C function reached two ways: a JNI wrapper and an FFM downcall.
 * Built by verify.sh:
 *   cc -shared -O2 -I"$JAVA_HOME/include" -I"$JAVA_HOME/include/darwin" \
 *      -o libnativeadd.dylib native_add.c
 */
#include <jni.h>

/* Unsigned add wraps like Java int addition; signed overflow is UB in C. */
int native_add(int a, int b) { return (int)((unsigned)a + (unsigned)b); }

JNIEXPORT jint JNICALL Java_example_Interop_jniAdd(JNIEnv *env, jclass cls,
                                                   jint a, jint b) {
    (void)env;
    (void)cls;
    return native_add(a, b);
}
