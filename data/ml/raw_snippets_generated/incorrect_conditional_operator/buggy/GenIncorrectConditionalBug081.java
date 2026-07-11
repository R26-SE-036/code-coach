public class GenIncorrectConditionalBug081 {
    static void announce(int stock) {
        if (stock = 5) {
            System.out.println("hit the target");
        }
    }
}
