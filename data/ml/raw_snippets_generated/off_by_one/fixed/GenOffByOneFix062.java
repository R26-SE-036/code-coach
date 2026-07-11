public class GenOffByOneFix062 {
    static int sum1(int[] ages) {
        int total = 0;
        for (int i = 0; i < ages.length; i++) {
            total += ages[i];
        }
        return total;
    }

    static int countAbove(int[] sizes, int threshold) {
        int hits = 0;
        for (int i = 0; i < sizes.length; i++) {
            if (sizes[i] > threshold) {
                hits++;
            }
        }
        return hits;
    }

    static int sum2(int[] prices) {
        int total = 0;
        for (int i = 0; i < prices.length; i++) {
            total += prices[i];
        }
        return total;
    }
}
