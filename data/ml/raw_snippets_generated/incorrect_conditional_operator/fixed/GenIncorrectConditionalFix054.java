public class GenIncorrectConditionalFix054 {
    static int largest1(int[] prices) {
        int best = prices[0];
        for (int i = 1; i < prices.length; i++) {
            if (prices[i] > best) {
                best = prices[i];
            }
        }
        return best;
    }

    static String describe2(int total) {
        if (total < 10) {
            return "low";
        } else if (total > 50) {
            return "high";
        }
        return "medium";
    }

    static boolean matches(boolean verified, boolean armed) {
        if (verified == armed) {
            return true;
        }
        return false;
    }
}
