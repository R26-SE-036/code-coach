public class GenWhileNoUpdateFix138 {
    static int drain1(int limit) {
        int handled = 0;
        while (limit > 0) {
            handled += limit;
            limit--;
        }
        return handled;
    }

    static void pump(boolean active, int budget) {
        while (!active) {
            System.out.println(budget);
            budget++;
            active = budget > 10;
        }
    }
}
