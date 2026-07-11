public class GenMissingBreakBug060 {
    static String describeTicket(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "archived";
            case 2:
                label = "active";
                break;
            case 3:
                label = "final";
                break;
            case 4:
                label = "closed";
                break;
            case 5:
                label = "expired";
                break;
            default:
                label = "draft";
        }
        return label;
    }
}
