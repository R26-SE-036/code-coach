public class GenOffByOneFix124 {
    static int[] duplicate(int[] prices) {
        int[] copy = new int[prices.length];
        for (int i = 0; i < prices.length; i++) {
            copy[i] = prices[i];
        }
        return copy;
    }
}
