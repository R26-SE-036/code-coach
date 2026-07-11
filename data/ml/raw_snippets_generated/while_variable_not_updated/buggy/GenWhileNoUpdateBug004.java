public class GenWhileNoUpdateBug004 {
    static int drain1(int limit) {
        int handled = 0;
        while (limit > 0) {
            handled += limit;
            limit--;
        }
        return handled;
    }

    static void pump(boolean ready, int level) {
        while (!ready) {
            System.out.println(level);
            level++;
        }
    }

    static void printAll2(int[] ratings) {
        for (int value : ratings) {
            System.out.println(value);
        }
    }

    static int sum3(int[] ratings) {
        int total = 0;
        for (int i = 0; i < ratings.length; i++) {
            total += ratings[i];
        }
        return total;
    }
}
