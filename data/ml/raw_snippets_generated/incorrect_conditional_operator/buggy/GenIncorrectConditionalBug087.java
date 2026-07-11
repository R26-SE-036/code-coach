public class GenIncorrectConditionalBug087 {
    static void announce(int limit) {
        if (limit = 10) {
            System.out.println("hit the target");
        }
    }
}
