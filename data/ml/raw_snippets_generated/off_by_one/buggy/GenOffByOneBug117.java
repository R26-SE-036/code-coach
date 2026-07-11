public class GenOffByOneBug117 {
    static int countAbove(int[] totals, int threshold) {
        int hits = 0;
        for (int i = 0; i <= totals.length; i++) {
            if (totals[i] > threshold) {
                hits++;
            }
        }
        return hits;
    }
}
