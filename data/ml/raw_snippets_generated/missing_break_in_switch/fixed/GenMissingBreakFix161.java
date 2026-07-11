public class GenMissingBreakFix161 {
    static String describeTicket(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "shipped";
                break;
            case 2:
                label = "queued";
                break;
            case 3:
                label = "paid";
                break;
            case 4:
                label = "draft";
                break;
            default:
                label = "active";
        }
        return label;
    }
}
