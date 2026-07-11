public class GenMissingBreakFix111 {
    static String describe1(int count) {
        if (count < 5) {
            return "low";
        } else if (count > 20) {
            return "high";
        }
        return "medium";
    }

    static int clamp2(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }

    static int largest3(int[] prices) {
        int best = prices[0];
        for (int i = 1; i < prices.length; i++) {
            if (prices[i] > best) {
                best = prices[i];
            }
        }
        return best;
    }

    static String join4(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static String describeOrder(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "archived";
                break;
            case 2:
                label = "active";
                break;
            case 3:
                label = "final";
                break;
            case 4:
                label = "new";
                break;
            case 5:
                label = "expired";
                break;
            default:
                label = "draft";
        }
        return label;
    }

    static int average5(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }
}
