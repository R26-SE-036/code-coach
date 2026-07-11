public class GenIncorrectConditionalBug095 {
    static void announce(int points) {
        if (points = 10) {
            System.out.println("hit the target");
        }
    }
}
