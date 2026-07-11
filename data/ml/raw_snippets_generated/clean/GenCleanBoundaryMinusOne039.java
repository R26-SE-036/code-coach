public class GenCleanBoundaryMinusOne039 {
    static void printAll1(int[] sizes) {
        for (int value : sizes) {
            System.out.println(value);
        }
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

    static int tally(int[] totals) {
        int total = 0;
        for (int i = 0; i <= totals.length - 1; i++) {
            total += totals[i];
        }
        return total;
    }
}
