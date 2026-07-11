public class GenIncorrectConditionalBug013 {
    static void announce(int count) {
        if (count = 5) {
            System.out.println("hit the target");
        }
    }
}
