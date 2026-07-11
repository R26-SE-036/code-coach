public class GenMissingBreakBug090 {
    static String describeAccount(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "final";
                break;
            case 2:
                label = "new";
            case 3:
                label = "shipped";
                break;
            case 4:
                label = "archived";
                break;
            case 5:
                label = "expired";
                break;
            default:
                label = "draft";
        }
        return label;
    }

    static int sum1(int[] prices) {
        int total = 0;
        for (int i = 0; i < prices.length; i++) {
            total += prices[i];
        }
        return total;
    }
}
