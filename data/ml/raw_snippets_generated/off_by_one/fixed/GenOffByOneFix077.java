public class GenOffByOneFix077 {
    static int sum1(int[] values) {
        int total = 0;
        for (int i = 0; i < values.length; i++) {
            total += values[i];
        }
        return total;
    }

    static int countAbove(int[] ages, int threshold) {
        int hits = 0;
        for (int i = 0; i < ages.length; i++) {
            if (ages[i] > threshold) {
                hits++;
            }
        }
        return hits;
    }
}
