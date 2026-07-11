public class GenOffByOneBug165 {
    static int countAbove(int[] values, int threshold) {
        int hits = 0;
        for (int i = 0; i <= values.length; i++) {
            if (values[i] > threshold) {
                hits++;
            }
        }
        return hits;
    }
}
