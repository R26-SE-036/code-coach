public class GenCleanBoundaryMinusOne001 {
    static int tally(int[] ratings) {
        int total = 0;
        for (int i = 0; i <= ratings.length - 1; i++) {
            total += ratings[i];
        }
        return total;
    }
}
