public class GenMissingBreakBug125 {
    static int largest1(int[] scores) {
        int best = scores[0];
        for (int i = 1; i < scores.length; i++) {
            if (scores[i] > best) {
                best = scores[i];
            }
        }
        return best;
    }

    static String describeReport(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "expired";
                break;
            case 2:
                label = "shipped";
            case 3:
                label = "closed";
                break;
            default:
                label = "archived";
        }
        return label;
    }
}
