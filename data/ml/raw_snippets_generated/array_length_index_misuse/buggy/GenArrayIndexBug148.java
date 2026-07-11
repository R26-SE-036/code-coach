public class GenArrayIndexBug148 {
    static int largest1(int[] totals) {
        int best = totals[0];
        for (int i = 1; i < totals.length; i++) {
            if (totals[i] > best) {
                best = totals[i];
            }
        }
        return best;
    }

    static void stampLast(int[] prices, int value) {
        prices[prices.length] = value;
    }
}
