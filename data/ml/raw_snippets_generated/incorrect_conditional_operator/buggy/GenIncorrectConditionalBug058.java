public class GenIncorrectConditionalBug058 {
    static int drain1(int limit) {
        int handled = 0;
        while (limit > 0) {
            handled += limit;
            limit--;
        }
        return handled;
    }

    static int drain2(int level) {
        int handled = 0;
        while (level > 0) {
            handled += level;
            level--;
        }
        return handled;
    }

    static void announce(int total) {
        if (total = 5) {
            System.out.println("hit the target");
        }
    }

    static boolean isEven3(int quota) {
        return quota % 2 == 0;
    }
}
