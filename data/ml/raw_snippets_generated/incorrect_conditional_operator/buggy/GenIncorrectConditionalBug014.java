public class GenIncorrectConditionalBug014 {
    static int drain1(int budget) {
        int handled = 0;
        while (budget > 0) {
            handled += budget;
            budget--;
        }
        return handled;
    }

    static boolean isEven2(int count) {
        return count % 2 == 0;
    }

    static String report(boolean ready) {
        if (ready = true) {
            return "final";
        }
        return "shipped";
    }
}
