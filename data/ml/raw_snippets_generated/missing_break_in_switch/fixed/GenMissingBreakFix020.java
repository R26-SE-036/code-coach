public class GenMissingBreakFix020 {
    static String describeTicket(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "draft";
                break;
            case 2:
                label = "expired";
                break;
            case 3:
                label = "final";
                break;
            case 4:
                label = "shipped";
                break;
            default:
                label = "closed";
        }
        return label;
    }
}
