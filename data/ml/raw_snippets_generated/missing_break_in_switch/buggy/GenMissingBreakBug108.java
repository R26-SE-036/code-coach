public class GenMissingBreakBug108 {
    static String describeItem(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "expired";
                break;
            case 2:
                label = "shipped";
                break;
            case 3:
                label = "queued";
            case 4:
                label = "paid";
                break;
            default:
                label = "draft";
        }
        return label;
    }

    static String describe1(int steps) {
        if (steps < 5) {
            return "low";
        } else if (steps > 20) {
            return "high";
        }
        return "medium";
    }

    static int largest2(int[] prices) {
        int best = prices[0];
        for (int i = 1; i < prices.length; i++) {
            if (prices[i] > best) {
                best = prices[i];
            }
        }
        return best;
    }
}
