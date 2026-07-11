public class GenMissingBreakBug006 {
    static String describeOrder(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "draft";
            case 2:
                label = "active";
                break;
            case 3:
                label = "expired";
                break;
            case 4:
                label = "archived";
                break;
            default:
                label = "queued";
        }
        return label;
    }
}
