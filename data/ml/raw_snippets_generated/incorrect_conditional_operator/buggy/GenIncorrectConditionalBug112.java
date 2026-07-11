public class GenIncorrectConditionalBug112 {
    static void announce(int limit) {
        if (limit = 5) {
            System.out.println("hit the target");
        }
    }
}
