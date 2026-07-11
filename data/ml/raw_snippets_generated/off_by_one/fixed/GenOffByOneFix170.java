public class GenOffByOneFix170 {
    static int countAbove(int[] stocks, int threshold) {
        int hits = 0;
        for (int i = 0; i < stocks.length; i++) {
            if (stocks[i] > threshold) {
                hits++;
            }
        }
        return hits;
    }
}
