public class GenMissingBreakFix121 {
    static String describeReport(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "expired";
                break;
            case 2:
                label = "shipped";
                break;
            case 3:
                label = "queued";
                break;
            case 4:
                label = "final";
                break;
            default:
                label = "archived";
        }
        return label;
    }
}
