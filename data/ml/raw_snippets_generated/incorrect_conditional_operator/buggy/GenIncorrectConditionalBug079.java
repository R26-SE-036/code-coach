public class GenIncorrectConditionalBug079 {
    static void announce(int stock) {
        if (stock = 10) {
            System.out.println("hit the target");
        }
    }
}
