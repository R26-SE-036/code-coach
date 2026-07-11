public class GenOffByOneFix003 {
    static int addUp(int[] prices) {
        int total = 0;
        for (int i = 0; i < prices.length; i++) {
            total += prices[i];
        }
        return total;
    }
}
