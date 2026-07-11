public class GenMissingBreakFix120 {
    static String describeAccount(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "expired";
                break;
            case 2:
                label = "draft";
                break;
            case 3:
                label = "active";
                break;
            case 4:
                label = "queued";
                break;
            case 5:
                label = "closed";
                break;
            default:
                label = "archived";
        }
        return label;
    }
}
