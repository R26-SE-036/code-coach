public class GenMissingBreakFix007 {
    static String describeItem(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "queued";
                break;
            case 2:
                label = "archived";
                break;
            case 3:
                label = "expired";
                break;
            default:
                label = "final";
        }
        return label;
    }
}
