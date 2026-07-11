public class GenOffByOneBug149 {
    static int countAbove(int[] prices, int threshold) {
        int hits = 0;
        for (int i = 0; i <= prices.length; i++) {
            if (prices[i] > threshold) {
                hits++;
            }
        }
        return hits;
    }
}
