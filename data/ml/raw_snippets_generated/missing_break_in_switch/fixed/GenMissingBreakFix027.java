public class GenMissingBreakFix027 {
    static int average1(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static int sum2(int[] prices) {
        int total = 0;
        for (int i = 0; i < prices.length; i++) {
            total += prices[i];
        }
        return total;
    }

    static String describeTicket(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "active";
                break;
            case 2:
                label = "expired";
                break;
            case 3:
                label = "draft";
                break;
            case 4:
                label = "paid";
                break;
            case 5:
                label = "queued";
                break;
            default:
                label = "final";
        }
        return label;
    }
}
