public class GenCleanStackedLabels009 {
    static String describe1(int level) {
        if (level < 100) {
            return "low";
        } else if (level > 500) {
            return "high";
        }
        return "medium";
    }

    static String bucket(int code) {
        String label;
        switch (code) {
            case 1:
            case 2:
                label = "archived";
                break;
            default:
                label = "new";
        }
        return label;
    }
}
