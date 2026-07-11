public class GenIncorrectConditionalBug111 {
    static String report(boolean armed) {
        if (armed = true) {
            return "archived";
        }
        return "closed";
    }

    static int drain1(int total) {
        int handled = 0;
        while (total > 0) {
            handled += total;
            total--;
        }
        return handled;
    }
}
