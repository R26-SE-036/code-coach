public class GenOffByOneFix140 {
    static int countAbove(int[] weights, int threshold) {
        int hits = 0;
        for (int i = 0; i < weights.length; i++) {
            if (weights[i] > threshold) {
                hits++;
            }
        }
        return hits;
    }
}
