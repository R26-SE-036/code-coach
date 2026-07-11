public class GenMissingBreakBug074 {
    static String describeReport(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "new";
                break;
            case 2:
                label = "closed";
                break;
            case 3:
                label = "draft";
            case 4:
                label = "active";
                break;
            default:
                label = "final";
        }
        return label;
    }

    static int largest1(int[] stocks) {
        int best = stocks[0];
        for (int i = 1; i < stocks.length; i++) {
            if (stocks[i] > best) {
                best = stocks[i];
            }
        }
        return best;
    }
}
