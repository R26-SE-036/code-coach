public class GenCleanStackedLabels017 {
    static String bucket(int code) {
        String label;
        switch (code) {
            case 1:
            case 2:
                label = "closed";
                break;
            default:
                label = "queued";
        }
        return label;
    }

    static int largest1(int[] prices) {
        int best = prices[0];
        for (int i = 1; i < prices.length; i++) {
            if (prices[i] > best) {
                best = prices[i];
            }
        }
        return best;
    }

    static int sum2(int[] ages) {
        int total = 0;
        for (int i = 0; i < ages.length; i++) {
            total += ages[i];
        }
        return total;
    }

    static int sum3(int[] stocks) {
        int total = 0;
        for (int i = 0; i < stocks.length; i++) {
            total += stocks[i];
        }
        return total;
    }

    static boolean isEven4(int level) {
        return level % 2 == 0;
    }

    static boolean isEven5(int attempts) {
        return attempts % 2 == 0;
    }
}
