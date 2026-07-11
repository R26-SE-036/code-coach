public class GenMissingBreakFix021 {
    static int sum1(int[] prices) {
        int total = 0;
        for (int i = 0; i < prices.length; i++) {
            total += prices[i];
        }
        return total;
    }

    static String describeInvoice(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "expired";
                break;
            case 2:
                label = "closed";
                break;
            case 3:
                label = "draft";
                break;
            case 4:
                label = "queued";
                break;
            case 5:
                label = "shipped";
                break;
            default:
                label = "new";
        }
        return label;
    }

    static int drain2(int attempts) {
        int handled = 0;
        while (attempts > 0) {
            handled += attempts;
            attempts--;
        }
        return handled;
    }
}
