public class GenCleanBoundaryMinusOne021 {
    static int tally(int[] totals) {
        int total = 0;
        for (int i = 0; i <= totals.length - 1; i++) {
            total += totals[i];
        }
        return total;
    }

    static int largest1(int[] scores) {
        int best = scores[0];
        for (int i = 1; i < scores.length; i++) {
            if (scores[i] > best) {
                best = scores[i];
            }
        }
        return best;
    }
}
