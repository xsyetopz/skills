import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.jar.Manifest;

/** Shows how java.util.jar.Manifest reads three malformed manifests. */
public final class ManifestNewlineCheck {
    private static Manifest read(String text) throws IOException {
        return new Manifest(new ByteArrayInputStream(
                text.getBytes(StandardCharsets.UTF_8)));
    }

    public static void main(String[] args) throws IOException {
        String head = "Manifest-Version: 1.0\n";
        Manifest noNewline = read(head + "Bundle-SymbolicName: a.b");
        System.out.println("no final newline, Bundle-SymbolicName = "
                + noNewline.getMainAttributes()
                        .getValue("Bundle-SymbolicName"));
        Manifest twoSpaces = read(head + "Require-Bundle: a,\n  b\n");
        System.out.println("two-space continuation, Require-Bundle = ["
                + twoSpaces.getMainAttributes().getValue("Require-Bundle")
                + "]");
        Manifest longLine = read(head + "Bundle-Name: "
                + "x".repeat(200) + "\n");
        System.out.println("200-byte line accepted, value length = "
                + longLine.getMainAttributes().getValue("Bundle-Name")
                        .length());
        try {
            read(head + "Require-Bundle: a,\nb\n");
        } catch (IOException e) {
            System.out.println("unindented continuation: " + e.getMessage());
        }
    }
}
