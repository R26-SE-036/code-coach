public class GenOffByOneFix135 {
    static int[] duplicate(int[] prices) {
        int[] copy = new int[prices.length];
        for (int i = 0; i < prices.length; i++) {
            copy[i] = prices[i];
        }
        return copy;
    }

    static int sum1(int[] values) {
        int total = 0;
        for (int i = 0; i < values.length; i++) {
            total += values[i];
        }
        return total;
    }

    static String status2(int code) {
        String label;
        switch (code) {
            case 1:
                label = "draft";
                break;
            case 2:
                label = "closed";
                break;
            default:
                label = "new";
        }
        return label;
    }

    static int largest3(int[] values) {
        int best = values[0];
        for (int i = 1; i < values.length; i++) {
            if (values[i] > best) {
                best = values[i];
            }
        }
        return best;
    }
}
