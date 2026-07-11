public class GenOffByOneFix159 {
    static int countAbove(int[] sizes, int threshold) {
        int hits = 0;
        for (int i = 0; i < sizes.length; i++) {
            if (sizes[i] > threshold) {
                hits++;
            }
        }
        return hits;
    }

    static int sum1(int[] totals) {
        int total = 0;
        for (int i = 0; i < totals.length; i++) {
            total += totals[i];
        }
        return total;
    }
}
