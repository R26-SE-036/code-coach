public class GenCleanGeneric075 {
    static String describe1(int limit) {
        if (limit < 10) {
            return "low";
        } else if (limit > 50) {
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

    static int drain3(int budget) {
        int handled = 0;
        while (budget > 0) {
            handled += budget;
            budget--;
        }
        return handled;
    }

    static int clamp4(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }
}
