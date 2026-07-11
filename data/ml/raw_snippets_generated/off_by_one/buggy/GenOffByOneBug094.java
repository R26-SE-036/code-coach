public class GenOffByOneBug094 {
    static int addUp(int[] totals) {
        int total = 0;
        for (int i = 0; i <= totals.length; i++) {
            total += totals[i];
        }
        return total;
    }
}
