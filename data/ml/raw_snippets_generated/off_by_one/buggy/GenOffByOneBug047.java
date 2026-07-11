public class GenOffByOneBug047 {
    static int average1(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static int addUp(int[] sizes) {
        int total = 0;
        for (int i = 0; i <= sizes.length; i++) {
            total += sizes[i];
        }
        return total;
    }

    static int largest2(int[] weights) {
        int best = weights[0];
        for (int i = 1; i < weights.length; i++) {
            if (weights[i] > best) {
                best = weights[i];
            }
        }
        return best;
    }
}
