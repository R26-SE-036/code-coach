public class GenOffByOneBug029 {
    static int[] duplicate(int[] values) {
        int[] copy = new int[values.length];
        for (int i = 0; i <= values.length; i++) {
            copy[i] = values[i];
        }
        return copy;
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

    static String status2(int code) {
        String label;
        switch (code) {
            case 1:
                label = "closed";
                break;
            case 2:
                label = "shipped";
                break;
            default:
                label = "paid";
        }
        return label;
    }

    static String status3(int code) {
        String label;
        switch (code) {
            case 1:
                label = "archived";
                break;
            case 2:
                label = "expired";
                break;
            default:
                label = "draft";
        }
        return label;
    }

    static String join4(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }
}
