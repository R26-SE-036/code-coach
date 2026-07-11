public class GenOffByOneFix130 {
    static int countAbove(int[] totals, int threshold) {
        int hits = 0;
        for (int i = 0; i < totals.length; i++) {
            if (totals[i] > threshold) {
                hits++;
            }
        }
        return hits;
    }

    static int sum1(int[] values) {
        int total = 0;
        for (int i = 0; i < values.length; i++) {
            total += values[i];
        }
        return total;
    }

    static int average2(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }
}
