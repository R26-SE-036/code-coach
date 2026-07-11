public class GenCleanBoundaryMinusOne031 {
    static int tally(int[] sizes) {
        int total = 0;
        for (int i = 0; i <= sizes.length - 1; i++) {
            total += sizes[i];
        }
        return total;
    }
}
