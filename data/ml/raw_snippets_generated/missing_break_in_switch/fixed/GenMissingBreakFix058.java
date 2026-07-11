public class GenMissingBreakFix058 {
    static String describeAccount(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "closed";
                break;
            case 2:
                label = "paid";
                break;
            case 3:
                label = "new";
                break;
            default:
                label = "final";
        }
        return label;
    }

    static String describe1(int total) {
        if (total < 10) {
            return "low";
        } else if (total > 50) {
            return "high";
        }
        return "medium";
    }
}
