public class GenCleanBoundaryMinusOne037 {
    static int largest1(int[] stocks) {
        int best = stocks[0];
        for (int i = 1; i < stocks.length; i++) {
            if (stocks[i] > best) {
                best = stocks[i];
            }
        }
        return best;
    }

    static int tally(int[] scores) {
        int total = 0;
        for (int i = 0; i <= scores.length - 1; i++) {
            total += scores[i];
        }
        return total;
    }
}
