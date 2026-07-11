public class GenCleanBoundaryMinusOne009 {
    static int tally(int[] scores) {
        int total = 0;
        for (int i = 0; i <= scores.length - 1; i++) {
            total += scores[i];
        }
        return total;
    }
}
