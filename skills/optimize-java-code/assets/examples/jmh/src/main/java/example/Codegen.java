package example;

import java.util.Arrays;
import jdk.incubator.vector.FloatVector;
import jdk.incubator.vector.VectorOperators;
import jdk.incubator.vector.VectorSpecies;

/** JIT code-generation constructs: dispatch, intrinsics, SIMD. */
public final class Codegen {
    private Codegen() {
    }

    /** Class hierarchy analysis: final versus effectively-leaf classes. */
    public static final class Leaf {
        /** Not final, but no subclass is ever loaded. */
        public static class OpenScaler {
            private final int factor;

            public OpenScaler(int factor) {
                this.factor = factor;
            }

            public int apply(int x) {
                return x * factor + 1;
            }
        }

        public static final class FinalScaler {
            private final int factor;

            public FinalScaler(int factor) {
                this.factor = factor;
            }

            public int apply(int x) {
                return x * factor + 1;
            }
        }

        private Leaf() {
        }

        public static long open(OpenScaler s, int[] xs) {
            long sum = 0;
            for (int x : xs) {
                sum += s.apply(x);
            }
            return sum;
        }

        public static long closed(FinalScaler s, int[] xs) {
            long sum = 0;
            for (int x : xs) {
                sum += s.apply(x);
            }
            return sum;
        }
    }

    /** Megamorphic call site versus a pattern switch on a sealed type. */
    public static final class Shapes {
        public sealed interface Shape
                permits Circle, Square, Rect, Triangle {
            double area();
        }

        public record Circle(double r) implements Shape {
            public double area() {
                return Math.PI * r * r;
            }
        }

        public record Square(double side) implements Shape {
            public double area() {
                return side * side;
            }
        }

        public record Rect(double w, double h) implements Shape {
            public double area() {
                return w * h;
            }
        }

        public record Triangle(double b, double h) implements Shape {
            public double area() {
                return 0.5 * b * h;
            }
        }

        private Shapes() {
        }

        public static double virtualSum(Shape[] shapes) {
            double sum = 0;
            for (Shape s : shapes) {
                sum += s.area();
            }
            return sum;
        }

        public static double switchSum(Shape[] shapes) {
            double sum = 0;
            for (Shape s : shapes) {
                sum += switch (s) {
                    case Circle c -> Math.PI * c.r() * c.r();
                    case Square q -> q.side() * q.side();
                    case Rect r -> r.w() * r.h();
                    case Triangle t -> 0.5 * t.b() * t.h();
                };
            }
            return sum;
        }

        public static Shape[] mixed(int n) {
            Shape[] shapes = new Shape[n];
            for (int i = 0; i < n; i++) {
                double v = 1 + (i % 17);
                shapes[i] = switch (i % 4) {
                    case 0 -> new Circle(v);
                    case 1 -> new Square(v);
                    case 2 -> new Rect(v, v + 1);
                    default -> new Triangle(v, v + 2);
                };
            }
            return shapes;
        }
    }

    /** JIT intrinsics in the class library. */
    public static final class Intrinsics {
        private Intrinsics() {
        }

        public static boolean manualEquals(byte[] a, byte[] b) {
            if (a.length != b.length) {
                return false;
            }
            for (int i = 0; i < a.length; i++) {
                if (a[i] != b[i]) {
                    return false;
                }
            }
            return true;
        }

        public static boolean libraryEquals(byte[] a, byte[] b) {
            return Arrays.equals(a, b);
        }

        public static int manualMismatch(byte[] a, byte[] b) {
            int n = Math.min(a.length, b.length);
            for (int i = 0; i < n; i++) {
                if (a[i] != b[i]) {
                    return i;
                }
            }
            return a.length == b.length ? -1 : n;
        }

        public static int libraryMismatch(byte[] a, byte[] b) {
            return Arrays.mismatch(a, b);
        }
    }

    /** Vector API (incubator, JEP 508 in JDK 25). */
    public static final class Simd {
        private static final VectorSpecies<Float> SPECIES =
            FloatVector.SPECIES_PREFERRED;

        private Simd() {
        }

        /** Strict left-to-right float sum: C2 must not reorder it. */
        public static float scalarDot(float[] a, float[] b) {
            float sum = 0f;
            for (int i = 0; i < a.length; i++) {
                sum += a[i] * b[i];
            }
            return sum;
        }

        /** Lane-wise partial sums: a different, reassociated order. */
        public static float vectorDot(float[] a, float[] b) {
            FloatVector acc = FloatVector.zero(SPECIES);
            int i = 0;
            int bound = SPECIES.loopBound(a.length);
            for (; i < bound; i += SPECIES.length()) {
                FloatVector va = FloatVector.fromArray(SPECIES, a, i);
                FloatVector vb = FloatVector.fromArray(SPECIES, b, i);
                acc = va.fma(vb, acc);
            }
            float sum = acc.reduceLanes(VectorOperators.ADD);
            for (; i < a.length; i++) {
                sum += a[i] * b[i];
            }
            return sum;
        }

        public static int lanes() {
            return SPECIES.length();
        }
    }
}
