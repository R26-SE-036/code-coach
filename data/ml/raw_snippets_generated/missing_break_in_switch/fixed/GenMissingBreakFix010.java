public class GenMissingBreakFix010 {
    static String describeTask(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "queued";
                break;
            case 2:
                label = "shipped";
                break;
            case 3:
                label = "draft";
                break;
            default:
                label = "expired";
        }
        return label;
    }

    static String describe1(int steps) {
        if (steps < 100) {
            return "low";
        } else if (steps > 500) {
            return "high";
        }
        return "medium";
    }
}
