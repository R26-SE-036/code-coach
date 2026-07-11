public class GenCleanBoundaryMinusOne030 {
    static int tally(int[] totals) {
        int total = 0;
        for (int i = 0; i <= totals.length - 1; i++) {
            total += totals[i];
        }
        return total;
    }

    static int average1(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }
}
