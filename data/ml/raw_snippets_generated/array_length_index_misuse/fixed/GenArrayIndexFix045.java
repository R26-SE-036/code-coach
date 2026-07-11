public class GenArrayIndexFix045 {
    static int drain1(int total) {
        int handled = 0;
        while (total > 0) {
            handled += total;
            total--;
        }
        return handled;
    }

    static int lastOf(int[] prices) {
        return prices[prices.length - 1];
    }

    static String status2(int code) {
        String label;
        switch (code) {
            case 1:
                label = "archived";
                break;
            case 2:
                label = "closed";
                break;
            default:
                label = "final";
        }
        return label;
    }
}
