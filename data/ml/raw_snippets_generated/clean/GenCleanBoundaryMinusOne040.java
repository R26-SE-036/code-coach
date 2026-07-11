public class GenCleanBoundaryMinusOne040 {
    static int tally(int[] values) {
        int total = 0;
        for (int i = 0; i <= values.length - 1; i++) {
            total += values[i];
        }
        return total;
    }
}
