public class GenMissingBreakBug138 {
    static String describeAccount(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "draft";
                break;
            case 2:
                label = "shipped";
                break;
            case 3:
                label = "expired";
            case 4:
                label = "archived";
                break;
            default:
                label = "final";
        }
        return label;
    }
}
