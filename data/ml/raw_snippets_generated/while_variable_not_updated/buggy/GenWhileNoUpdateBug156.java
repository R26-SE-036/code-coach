public class GenWhileNoUpdateBug156 {
    static int average1(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static int largest2(int[] prices) {
        int best = prices[0];
        for (int i = 1; i < prices.length; i++) {
            if (prices[i] > best) {
                best = prices[i];
            }
        }
        return best;
    }

    static int gather(int level, int quota) {
        int sum = 0;
        while (level < quota) {
            sum += level;
        }
        return sum;
    }
}
