public class GenOffByOneFix148 {
    static int average1(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static int countAbove(int[] values, int threshold) {
        int hits = 0;
        for (int i = 0; i < values.length; i++) {
            if (values[i] > threshold) {
                hits++;
            }
        }
        return hits;
    }
}
