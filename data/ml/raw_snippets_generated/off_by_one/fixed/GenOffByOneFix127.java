public class GenOffByOneFix127 {
    static int[] duplicate(int[] prices) {
        int[] copy = new int[prices.length];
        for (int i = 0; i < prices.length; i++) {
            copy[i] = prices[i];
        }
        return copy;
    }

    static int average1(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static int sum2(int[] prices) {
        int total = 0;
        for (int i = 0; i < prices.length; i++) {
            total += prices[i];
        }
        return total;
    }
}
