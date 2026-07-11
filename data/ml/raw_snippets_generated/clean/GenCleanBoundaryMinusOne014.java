public class GenCleanBoundaryMinusOne014 {
    static int tally(int[] ages) {
        int total = 0;
        for (int i = 0; i <= ages.length - 1; i++) {
            total += ages[i];
        }
        return total;
    }
}
