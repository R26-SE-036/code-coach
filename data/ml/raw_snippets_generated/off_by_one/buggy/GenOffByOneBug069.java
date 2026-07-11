public class GenOffByOneBug069 {
    static int countAbove(int[] prices, int threshold) {
        int hits = 0;
        for (int i = 0; i <= prices.length; i++) {
            if (prices[i] > threshold) {
                hits++;
            }
        }
        return hits;
    }

    static void printAll1(int[] stocks) {
        for (int value : stocks) {
            System.out.println(value);
        }
    }

    static int largest2(int[] sizes) {
        int best = sizes[0];
        for (int i = 1; i < sizes.length; i++) {
            if (sizes[i] > best) {
                best = sizes[i];
            }
        }
        return best;
    }
}
