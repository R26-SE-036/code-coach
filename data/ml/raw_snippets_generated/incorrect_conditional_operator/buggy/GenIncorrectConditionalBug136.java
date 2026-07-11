public class GenIncorrectConditionalBug136 {
    static void announce(int attempts) {
        if (attempts = 100) {
            System.out.println("hit the target");
        }
    }
}
