public class GenMissingBreakBug048 {
    static String describeAccount(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "closed";
                break;
            case 2:
                label = "shipped";
                break;
            case 3:
                label = "archived";
            case 4:
                label = "expired";
                break;
            case 5:
                label = "final";
                break;
            default:
                label = "queued";
        }
        return label;
    }
}
