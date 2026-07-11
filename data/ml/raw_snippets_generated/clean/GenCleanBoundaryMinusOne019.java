public class GenCleanBoundaryMinusOne019 {
    static int clamp1(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static String describe2(int total) {
        if (total < 100) {
            return "low";
        } else if (total > 500) {
            return "high";
        }
        return "medium";
    }

    static int tally(int[] prices) {
        int total = 0;
        for (int i = 0; i <= prices.length - 1; i++) {
            total += prices[i];
        }
        return total;
    }

    static int largest3(int[] prices) {
        int best = prices[0];
        for (int i = 1; i < prices.length; i++) {
            if (prices[i] > best) {
                best = prices[i];
            }
        }
        return best;
    }

    static int drain4(int attempts) {
        int handled = 0;
        while (attempts > 0) {
            handled += attempts;
            attempts--;
        }
        return handled;
    }

    static int clamp5(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }
}
