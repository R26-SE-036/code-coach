public class GenCleanBoundaryMinusOne029 {
    static int tally(int[] totals) {
        int total = 0;
        for (int i = 0; i <= totals.length - 1; i++) {
            total += totals[i];
        }
        return total;
    }
}
