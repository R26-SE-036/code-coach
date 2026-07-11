public class GenOffByOneBug050 {
    static int sum1(int[] totals) {
        int total = 0;
        for (int i = 0; i < totals.length; i++) {
            total += totals[i];
        }
        return total;
    }

    static boolean isEven2(int budget) {
        return budget % 2 == 0;
    }

    static int countAbove(int[] stocks, int threshold) {
        int hits = 0;
        for (int i = 0; i <= stocks.length; i++) {
            if (stocks[i] > threshold) {
                hits++;
            }
        }
        return hits;
    }
}
