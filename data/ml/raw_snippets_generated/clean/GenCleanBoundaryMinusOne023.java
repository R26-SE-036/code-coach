public class GenCleanBoundaryMinusOne023 {
    static int tally(int[] stocks) {
        int total = 0;
        for (int i = 0; i <= stocks.length - 1; i++) {
            total += stocks[i];
        }
        return total;
    }
}
