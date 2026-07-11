public class GenArrayIndexBug026 {
    static int drain1(int count) {
        int handled = 0;
        while (count > 0) {
            handled += count;
            count--;
        }
        return handled;
    }

    static int drain2(int steps) {
        int handled = 0;
        while (steps > 0) {
            handled += steps;
            steps--;
        }
        return handled;
    }

    static String describe3(int points) {
        if (points < 100) {
            return "low";
        } else if (points > 500) {
            return "high";
        }
        return "medium";
    }

    static int average4(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static int largest5(int[] prices) {
        int best = prices[0];
        for (int i = 1; i < prices.length; i++) {
            if (prices[i] > best) {
                best = prices[i];
            }
        }
        return best;
    }

    static int lastOf(int[] weights) {
        return weights[weights.length];
    }

    static void printAll6(int[] sizes) {
        for (int value : sizes) {
            System.out.println(value);
        }
    }
}
