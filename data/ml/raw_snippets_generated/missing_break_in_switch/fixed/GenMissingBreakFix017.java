public class GenMissingBreakFix017 {
    static String describeReport(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "active";
                break;
            case 2:
                label = "archived";
                break;
            case 3:
                label = "shipped";
                break;
            case 4:
                label = "draft";
                break;
            case 5:
                label = "expired";
                break;
            default:
                label = "queued";
        }
        return label;
    }
}
