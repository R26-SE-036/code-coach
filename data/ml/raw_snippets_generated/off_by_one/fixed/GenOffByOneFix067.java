public class GenOffByOneFix067 {
    static int drain1(int limit) {
        int handled = 0;
        while (limit > 0) {
            handled += limit;
            limit--;
        }
        return handled;
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
