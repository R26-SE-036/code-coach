public class GenIncorrectConditionalBug145 {
    static void announce(int steps) {
        if (steps = 100) {
            System.out.println("hit the target");
        }
    }
}
