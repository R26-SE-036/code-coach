public class GenIncorrectConditionalBug121 {
    static void announce(int count) {
        if (count = 100) {
            System.out.println("hit the target");
        }
    }
}
