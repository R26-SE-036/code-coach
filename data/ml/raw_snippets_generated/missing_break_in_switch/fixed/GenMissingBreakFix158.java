public class GenMissingBreakFix158 {
    static String describeTicket(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "new";
                break;
            case 2:
                label = "shipped";
                break;
            case 3:
                label = "expired";
                break;
            case 4:
                label = "draft";
                break;
            case 5:
                label = "queued";
                break;
            default:
                label = "active";
        }
        return label;
    }
}
