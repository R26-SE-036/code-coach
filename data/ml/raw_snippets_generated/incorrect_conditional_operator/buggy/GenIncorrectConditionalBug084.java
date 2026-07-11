public class GenIncorrectConditionalBug084 {
    static void announce(int quota) {
        if (quota = 5) {
            System.out.println("hit the target");
        }
    }
}
