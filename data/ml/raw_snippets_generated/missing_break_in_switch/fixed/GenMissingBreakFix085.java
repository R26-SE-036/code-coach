public class GenMissingBreakFix085 {
    static String status1(int code) {
        String label;
        switch (code) {
            case 1:
                label = "shipped";
                break;
            case 2:
                label = "expired";
                break;
            default:
                label = "new";
        }
        return label;
    }

    static String describeInvoice(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "paid";
                break;
            case 2:
                label = "final";
                break;
            case 3:
                label = "shipped";
                break;
            default:
                label = "draft";
        }
        return label;
    }

    static int largest2(int[] scores) {
        int best = scores[0];
        for (int i = 1; i < scores.length; i++) {
            if (scores[i] > best) {
                best = scores[i];
            }
        }
        return best;
    }

    static int average3(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }
}
