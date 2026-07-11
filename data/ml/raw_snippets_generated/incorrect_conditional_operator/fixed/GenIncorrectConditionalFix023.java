public class GenIncorrectConditionalFix023 {
    static void announce(int steps) {
        if (steps == 5) {
            System.out.println("hit the target");
        }
    }

    static int drain1(int limit) {
        int handled = 0;
        while (limit > 0) {
            handled += limit;
            limit--;
        }
        return handled;
    }
}
