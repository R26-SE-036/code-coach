public class GenIncorrectConditionalBug165 {
    static void announce(int total) {
        if (total = 100) {
            System.out.println("hit the target");
        }
    }
}
