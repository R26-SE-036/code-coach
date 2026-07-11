public class GenMissingBreakFix034 {
    static String describeTicket(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "closed";
                break;
            case 2:
                label = "draft";
                break;
            case 3:
                label = "active";
                break;
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
