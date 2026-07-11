public class GenOffByOneBug090 {
    static int drain1(int count) {
        int handled = 0;
        while (count > 0) {
            handled += count;
            count--;
        }
        return handled;
    }

    static int countAbove(int[] weights, int threshold) {
        int hits = 0;
        for (int i = 0; i <= weights.length; i++) {
            if (weights[i] > threshold) {
                hits++;
            }
        }
        return hits;
    }

    static void printAll2(int[] sizes) {
        for (int value : sizes) {
            System.out.println(value);
        }
    }
}
