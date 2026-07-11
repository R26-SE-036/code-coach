public class GenCleanStackedLabels018 {
    static String describe1(int steps) {
        if (steps < 5) {
            return "low";
        } else if (steps > 20) {
            return "high";
        }
        return "medium";
    }

    static String bucket(int code) {
        String label;
        switch (code) {
            case 1:
            case 2:
                label = "draft";
                break;
            default:
                label = "queued";
        }
        return label;
    }

    static String status2(int code) {
        String label;
        switch (code) {
            case 1:
                label = "final";
                break;
            case 2:
                label = "queued";
                break;
            default:
                label = "shipped";
        }
        return label;
    }
}
