public class GenIncorrectConditionalBug041 {
    static void announce(int attempts) {
        if (attempts = 10) {
            System.out.println("hit the target");
        }
    }
}
