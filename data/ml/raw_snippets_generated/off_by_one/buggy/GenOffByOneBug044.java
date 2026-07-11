public class GenOffByOneBug044 {
    static int addUp(int[] sizes) {
        int total = 0;
        for (int i = 0; i <= sizes.length; i++) {
            total += sizes[i];
        }
        return total;
    }

    static String describe1(int level) {
        if (level < 100) {
            return "low";
        } else if (level > 500) {
            return "high";
        }
        return "medium";
    }

    static int sum2(int[] ratings) {
        int total = 0;
        for (int i = 0; i < ratings.length; i++) {
            total += ratings[i];
        }
        return total;
    }

    static int drain3(int limit) {
        int handled = 0;
        while (limit > 0) {
            handled += limit;
            limit--;
        }
        return handled;
    }
}
