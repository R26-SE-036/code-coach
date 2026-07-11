public class GenIncorrectConditionalFix116 {
    static int largest1(int[] prices) {
        int best = prices[0];
        for (int i = 1; i < prices.length; i++) {
            if (prices[i] > best) {
                best = prices[i];
            }
        }
        return best;
    }

    static boolean matches(boolean valid, boolean verified) {
        if (valid == verified) {
            return true;
        }
        return false;
    }
}
