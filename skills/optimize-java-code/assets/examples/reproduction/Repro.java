import java.util.HashMap;
import java.util.Map;
public final class Repro {
  public static void main(String[] args) {
    Integer first = Integer.valueOf(1000);
    Integer second = Integer.valueOf(1000);
    System.out.println("actual identity=" + (first == second));
    System.out.println("expected numeric equality=" + first.equals(second));
    if (first == second || !first.equals(second)) throw new AssertionError();
  }
}
