// XML external entity pair for DocumentBuilderFactory (CWE-611).
// Run: java Xxe.java vulnerable|fixed SECRET_FILE
// The "vulnerable" mode is INTENTIONALLY VULNERABLE: JDK defaults resolve
// external entities, so the document can read SECRET_FILE.
import java.io.ByteArrayInputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import javax.xml.XMLConstants;
import javax.xml.parsers.DocumentBuilderFactory;

public class Xxe {
    static DocumentBuilderFactory factory(boolean fixed) throws Exception {
        DocumentBuilderFactory f = DocumentBuilderFactory.newInstance();
        if (fixed) {
            f.setFeature(
                "http://apache.org/xml/features/disallow-doctype-decl", true);
            f.setFeature(XMLConstants.FEATURE_SECURE_PROCESSING, true);
            f.setXIncludeAware(false);
            f.setExpandEntityReferences(false);
        }
        return f;
    }

    public static void main(String[] args) throws Exception {
        boolean fixed = args[0].equals("fixed");
        String uri = Path.of(args[1]).toUri().toString();
        String xml = "<?xml version=\"1.0\"?>"
            + "<!DOCTYPE r [<!ENTITY x SYSTEM \"" + uri + "\">]><r>&x;</r>";
        var input = new ByteArrayInputStream(
            xml.getBytes(StandardCharsets.UTF_8));
        try {
            var doc = factory(fixed).newDocumentBuilder().parse(input);
            String text = doc.getDocumentElement().getTextContent();
            System.out.println("parsed text=" + text.strip());
        } catch (org.xml.sax.SAXParseException e) {
            System.out.println("rejected: " + e.getMessage());
        }
        var ok = new ByteArrayInputStream(
            "<r>ok</r>".getBytes(StandardCharsets.UTF_8));
        var plain = factory(fixed).newDocumentBuilder().parse(ok);
        System.out.println("plain text="
            + plain.getDocumentElement().getTextContent());
    }
}
