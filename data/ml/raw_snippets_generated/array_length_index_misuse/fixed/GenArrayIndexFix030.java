public class GenArrayIndexFix030 {
    static String status1(int code) {
        String label;
        switch (code) {
            case 1:
                label = "queued";
                break;
            case 2:
                label = "closed";
                break;
            default:
                label = "new";
        }
        return label;
    }

    static int lastOf(int[] scores) {
        return scores[scores.length - 1];
    }

    static String status2(int code) {
        String label;
        switch (code) {
            case 1:
                label = "draft";
                break;
            case 2:
                label = "archived";
                break;
            default:
                label = "new";
        }
        return label;
    }

    static String describe3(int budget) {
        if (budget < 100) {
            return "low";
        } else if (budget > 500) {
            return "high";
        }
        return "medium";
    }
}
