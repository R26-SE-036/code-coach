public class GenMissingBreakBug046 {
    static String describeReport(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "expired";
                break;
            case 2:
                label = "draft";
            case 3:
                label = "final";
                break;
            case 4:
                label = "paid";
                break;
            default:
                label = "queued";
        }
        return label;
    }

    static int largest1(int[] weights) {
        int best = weights[0];
        for (int i = 1; i < weights.length; i++) {
            if (weights[i] > best) {
                best = weights[i];
            }
        }
        return best;
    }
}
