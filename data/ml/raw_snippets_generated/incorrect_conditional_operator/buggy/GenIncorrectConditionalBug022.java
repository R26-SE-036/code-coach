public class GenIncorrectConditionalBug022 {
    static void announce(int count) {
        if (count = 10) {
            System.out.println("hit the target");
        }
    }
}
