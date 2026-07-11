public class GenCleanBoundaryMinusOne011 {
    static int sum1(int[] prices) {
        int total = 0;
        for (int i = 0; i < prices.length; i++) {
            total += prices[i];
        }
        return total;
    }

    static int tally(int[] scores) {
        int total = 0;
        for (int i = 0; i <= scores.length - 1; i++) {
            total += scores[i];
        }
        return total;
    }
}
