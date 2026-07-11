public class GenMissingBreakFix113 {
    static String describe1(int attempts) {
        if (attempts < 5) {
            return "low";
        } else if (attempts > 20) {
            return "high";
        }
        return "medium";
    }

    static String describeOrder(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "paid";
                break;
            case 2:
                label = "queued";
                break;
            case 3:
                label = "archived";
                break;
            case 4:
                label = "new";
                break;
            default:
                label = "expired";
        }
        return label;
    }

    static int sum2(int[] scores) {
        int total = 0;
        for (int i = 0; i < scores.length; i++) {
            total += scores[i];
        }
        return total;
    }
}
