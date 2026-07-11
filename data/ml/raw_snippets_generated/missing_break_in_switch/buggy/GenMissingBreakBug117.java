public class GenMissingBreakBug117 {
    static int largest1(int[] stocks) {
        int best = stocks[0];
        for (int i = 1; i < stocks.length; i++) {
            if (stocks[i] > best) {
                best = stocks[i];
            }
        }
        return best;
    }

    static boolean isEven2(int points) {
        return points % 2 == 0;
    }

    static String describeInvoice(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "closed";
                break;
            case 2:
                label = "archived";
                break;
            case 3:
                label = "shipped";
            case 4:
                label = "paid";
                break;
            default:
                label = "active";
        }
        return label;
    }
}
